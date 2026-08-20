import csv
import io
import re
from decimal import Decimal, InvalidOperation

from django import forms
from django.db import transaction

from .models import Item, Source, Bin, InventoryBalance, InventoryMovement


class ItemCSVImportForm(forms.Form):
    csv_file = forms.FileField()
    set_quantities = forms.BooleanField(
        required=False,
        initial=True,
        help_text="If checked, quantity column will set the DEFAULT bin quantity (creates ADJUST movements).",
    )


def _normalize_header(h: str) -> str:
    if h is None:
        return ""

    h = str(h).strip().lower()
    h = h.replace("\ufeff", "")
    h = h.replace(" ", "_").replace("-", "_")
    h = re.sub(r"_+", "_", h)
    return h


def _to_decimal(val, default=Decimal("0.00")):
    if val is None:
        return default

    s = str(val).strip()
    if not s:
        return default

    s = s.replace("$", "").replace(",", "")

    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return default


def _to_int(val, default=0):
    if val is None:
        return default

    s = str(val).strip()
    if not s:
        return default

    s = s.replace(",", "").replace("$", "")

    try:
        return int(float(s))
    except (ValueError, TypeError):
        return default


def _get_default_bin():
    src, _ = Source.objects.get_or_create(
        name="Main Facility",
        defaults={"is_main_facility": True},
    )

    b, _ = Bin.objects.get_or_create(
        code="DEFAULT",
        defaults={"location": src},
    )

    return b


def _read_uploaded_file_to_text(file_obj) -> str:
    try:
        file_obj.seek(0)
    except Exception:
        pass

    raw = file_obj.read()

    if isinstance(raw, (bytes, bytearray)):
        raw = raw.replace(b"\x00", b"")

    try:
        return raw.decode("utf-8-sig")
    except Exception:
        return raw.decode("latin-1", errors="replace")


def _find_qty(row: dict) -> int:
    qty_keys = (
        "starting_qty",
        "starting_quantity",
        "start_qty",
        "start_quantity",
        "qty",
        "quantity",
        "on_hand",
        "onhand",
        "on_hand_qty",
        "on_hand_quantity",
        "available_qty",
        "available_quantity",
        "stock",
        "stock_qty",
        "stock_quantity",
    )

    for key in qty_keys:
        if key in row and str(row.get(key, "")).strip() != "":
            return _to_int(row.get(key), default=0)

    return 0


def _extract_sku_suffix(sku: str) -> str:
    """
    Example:
        TSWP91#1711 -> 1711
        TSWJ114P91A12#1711 -> 1711
    """
    sku = (sku or "").strip()

    if "#" not in sku:
        return ""

    return sku.rsplit("#", 1)[1].strip()


def _find_bin_from_sku(sku: str):
    """
    Find the warehouse Bin encoded at the end of the SKU prefix.

    We match against real WMS Bin codes instead of guessing with a regex.

    Examples:
        TSWRVABA3#4596 -> BA3
        TSWJ114P91A12#1711 -> A12
        TSWXYZF61#1234 -> F61

    If more than one bin code could match, the longest match wins.
    """
    sku = (sku or "").strip()

    if "#" not in sku:
        return None

    prefix = sku.rsplit("#", 1)[0].upper()

    bins = list(
        Bin.objects.exclude(code__isnull=True)
        .exclude(code="")
        .select_related("location")
    )

    matches = []

    for bin_obj in bins:
        code = (bin_obj.code or "").strip().upper()

        if code and prefix.endswith(code):
            matches.append(bin_obj)

    if not matches:
        return None

    matches.sort(
        key=lambda b: len((b.code or "").strip()),
        reverse=True,
    )

    return matches[0]


def _find_ebay_item_number(row: dict) -> str:
    """
    Supports common eBay export column names.

    'Item number' becomes 'item_number' after header normalization.
    """
    possible_keys = (
        "ebay_item_number",
        "item_number",
        "ebay_item_id",
        "item_id",
        "listing_id",
    )

    for key in possible_keys:
        value = str(row.get(key, "") or "").strip()

        if value:
            # Excel sometimes turns IDs into values like 123456789012.0
            if re.fullmatch(r"\d+\.0", value):
                value = value[:-2]

            return value

    return ""


def _find_existing_item(sku: str, sku_suffix: str, ebay_item_number: str):
    """
    Safely identify the existing WMS Item.

    Match priority:

    1. eBay Item Number
    2. Exact full SKU
    3. Unique final # suffix only

    Never guess when multiple WMS records share a suffix.
    """

    # -------------------------------------------------
    # 1. Permanent eBay identity is the strongest match
    # -------------------------------------------------
    if ebay_item_number:
        obj = Item.objects.filter(
            ebay_item_number=ebay_item_number
        ).first()

        if obj:
            return obj, "ebay_item_number"

    # -------------------------------------------------
    # 2. Exact full SKU
    # -------------------------------------------------
    exact_matches = Item.objects.filter(
        sku=sku
    ).order_by("id")

    exact_count = exact_matches.count()

    if exact_count == 1:
        return exact_matches.first(), "exact_sku"

    if exact_count > 1:
        raise ValueError(
            f"Duplicate exact SKU {sku}: "
            f"{exact_count} WMS records use this exact SKU."
        )

    # -------------------------------------------------
    # 3. Final # suffix only when unique
    # -------------------------------------------------
    if sku_suffix:
        # Match both current "#7883" and legacy "# 7883" formatting.
        suffix_candidates = Item.objects.filter(
            sku__contains="#"
        ).order_by("id")

        suffix_matches = []

        for candidate in suffix_candidates:
            candidate_sku = (candidate.sku or "").strip()

            if "#" not in candidate_sku:
                continue

            candidate_suffix = candidate_sku.rsplit("#", 1)[1].strip()

            if candidate_suffix == sku_suffix:
                suffix_matches.append(candidate)

        suffix_count = len(suffix_matches)

        if suffix_count == 1:
            return suffix_matches[0], "sku_suffix"

        if suffix_count > 1:
            raise ValueError(
                f"Ambiguous SKU suffix #{sku_suffix}: "
                f"{suffix_count} WMS items use this suffix. "
                "An exact SKU or eBay Item Number is required."
            )

    return None, "new"


@transaction.atomic
def import_items_from_csv(file_obj, set_quantities: bool, user=None):
    created = 0
    updated = 0
    errors = []

    text = _read_uploaded_file_to_text(file_obj)

    buf = io.StringIO(text)
    reader = csv.DictReader(buf)

    if not reader.fieldnames:
        return {
            "created": 0,
            "updated": 0,
            "errors": ["CSV has no header row."],
        }

    reader.fieldnames = [
        _normalize_header(h)
        for h in reader.fieldnames
    ]

    if "sku" not in reader.fieldnames:
        return {
            "created": 0,
            "updated": 0,
            "errors": [
                f"Missing required column: sku. Found columns: {reader.fieldnames}"
            ],
        }

    default_bin = _get_default_bin() if set_quantities else None

    performed_by = (
        user
        if user and getattr(user, "is_authenticated", False)
        else None
    )

    for idx, row in enumerate(reader, start=2):
        try:
            with transaction.atomic():
                clean_row = {}

                for k, v in (row or {}).items():
                    nk = _normalize_header(k)
                    nv = "" if v is None else str(v).strip()
                    clean_row[nk] = nv

                sku = clean_row.get("sku", "").strip()

                if not sku:
                    continue

                # Normalize whitespace immediately after the final #.
                # Examples:
                #   TSWRVABA3#4596   -> TSWRVABA3#4596
                #   TSWRVABA3# 4596  -> TSWRVABA3#4596
                #   TSWRVABA3#   4596 -> TSWRVABA3#4596
                if "#" in sku:
                    sku_prefix, sku_number = sku.rsplit("#", 1)
                    sku = f"{sku_prefix.rstrip()}#{sku_number.strip()}"

                sku_suffix = _extract_sku_suffix(sku)
                ebay_item_number = _find_ebay_item_number(clean_row)

                name = clean_row.get("name", "").strip() or sku

                # Some eBay exports call the title "Title".
                if not clean_row.get("name", "").strip():
                    name = clean_row.get("title", "").strip() or sku

                price = _to_decimal(
                    clean_row.get("price"),
                    default=Decimal("0.00"),
                )

                # Common eBay export alternatives for price.
                if price == Decimal("0.00"):
                    for price_key in (
                        "current_price",
                        "start_price",
                        "buy_it_now_price",
                    ):
                        if clean_row.get(price_key, "").strip():
                            price = _to_decimal(
                                clean_row.get(price_key),
                                default=Decimal("0.00"),
                            )
                            break

                defaults = {
                    "name": name,
                    "price": price,
                    "condition": clean_row.get("condition", "").strip(),
                    "description": clean_row.get("description", "").strip(),
                    "image_url": clean_row.get("image_url", "").strip(),
                    "listing_url": clean_row.get("listing_url", "").strip(),
                    "source": clean_row.get("source", "").strip() or "Manual",
                    "location": clean_row.get("location", "").strip(),
                }

                obj, match_method = _find_existing_item(
                    sku=sku,
                    sku_suffix=sku_suffix,
                    ebay_item_number=ebay_item_number,
                )

                if obj is None:
                    obj = Item(
                        sku=sku,
                        ebay_item_number=ebay_item_number or None,
                        **defaults,
                    )
                    obj.save()
                    row_created = True

                else:
                    # IMPORTANT:
                    # If eBay changed the location/prefix portion of the SKU,
                    # update the existing WMS Item instead of creating another.
                    obj.sku = sku

                    if ebay_item_number:
                        obj.ebay_item_number = ebay_item_number

                    for field_name, value in defaults.items():
                        setattr(obj, field_name, value)

                    obj.save()
                    row_created = False

                # ----------------------------
                # Quantities / SKU-derived Bin
                # ----------------------------
                if set_quantities:
                    target_qty = max(
                        0,
                        _find_qty(clean_row),
                    )

                    sku_bin = _find_bin_from_sku(sku)

                    # Use the SKU-derived warehouse bin when possible.
                    # Fall back to DEFAULT if no existing WMS bin matches.
                    target_bin = sku_bin or default_bin

                    stocked_balances = list(
                        InventoryBalance.objects.filter(
                            item=obj,
                            quantity__gt=0,
                        ).select_related("bin")
                    )

                    stocked_other_bins = [
                        bal
                        for bal in stocked_balances
                        if bal.bin_id != target_bin.id
                    ]

                    target_bal = next(
                        (
                            bal
                            for bal in stocked_balances
                            if bal.bin_id == target_bin.id
                        ),
                        None,
                    )

                    # -------------------------------------------------
                    # MULTI-LOCATION SAFETY
                    # -------------------------------------------------
                    # If stock already exists in more than one bin and
                    # the SKU points to a different location, do not
                    # consolidate automatically.
                    #
                    # Preserve existing physical bin when incoming SKU
                    # does not contain a warehouse/bin location.
                    if (
                        sku_bin is None
                        and len(stocked_balances) == 1
                        and len(stocked_other_bins) == 1
                    ):
                        target_bin = stocked_other_bins[0].bin
                        target_bal = stocked_other_bins[0]
                    # Physical split inventory must be reviewed manually.
                    # -------------------------------------------------
                    if len(stocked_balances) > 1 and stocked_other_bins:
                        raise ValueError(
                            f"Item already has stock in multiple bins "
                            f"({', '.join(b.bin.code for b in stocked_balances)}). "
                            f"SKU points to {target_bin.code}; automatic relocation skipped."
                        )

                    # -------------------------------------------------
                    # Single existing stocked bin -> move to new SKU bin
                    # -------------------------------------------------
                    if (
                        len(stocked_balances) == 1
                        and stocked_other_bins
                        and sku_bin is not None
                    ):
                        old_bal = stocked_other_bins[0]
                        old_qty = int(old_bal.quantity or 0)

                        if old_qty > 0:
                            InventoryMovement.objects.create(
                                item=obj,
                                from_bin=old_bal.bin,
                                to_bin=target_bin,
                                movement_type="TRANSFER",
                                quantity=old_qty,
                                note=f"CSV import moved stock based on SKU bin {target_bin.code}",
                                performed_by=performed_by,
                            )

                            InventoryBalance.objects.filter(
                                pk=old_bal.pk
                            ).update(
                                quantity=0
                            )

                            target_bal, _ = InventoryBalance.objects.get_or_create(
                                item=obj,
                                bin=target_bin,
                                defaults={"quantity": 0},
                            )

                            InventoryBalance.objects.filter(
                                pk=target_bal.pk
                            ).update(
                                quantity=old_qty
                            )

                    # Ensure a balance exists in the target bin.
                    target_bal, _ = InventoryBalance.objects.get_or_create(
                        item=obj,
                        bin=target_bin,
                        defaults={"quantity": 0},
                    )

                    target_bal.refresh_from_db()

                    current_qty = int(target_bal.quantity or 0)
                    delta = target_qty - current_qty

                    if delta != 0:
                        if delta > 0:
                            InventoryMovement.objects.create(
                                item=obj,
                                from_bin=None,
                                to_bin=target_bin,
                                movement_type="ADJUST",
                                quantity=delta,
                                note="CSV import set quantity",
                                performed_by=performed_by,
                            )

                        else:
                            InventoryMovement.objects.create(
                                item=obj,
                                from_bin=target_bin,
                                to_bin=None,
                                movement_type="ADJUST",
                                quantity=(-delta),
                                note="CSV import set quantity",
                                performed_by=performed_by,
                            )

                    # Keep final target-bin balance equal to the CSV quantity.
                    InventoryBalance.objects.filter(
                        pk=target_bal.pk
                    ).update(
                        quantity=target_qty
                    )

                    # Keep Item display fields aligned with the derived bin.
                    if sku_bin is not None:
                        Item.objects.filter(pk=obj.pk).update(
                            current_bin=target_bin,
                            location=target_bin.code,
                        )

                # Count this row only after every DB operation succeeded.
                if row_created:
                    created += 1
                else:
                    updated += 1

        except Exception as e:
            errors.append(
                f"Line {idx}: {e}"
            )

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
    }

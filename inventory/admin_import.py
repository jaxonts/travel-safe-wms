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
        initial=False,
        help_text="If checked, quantity column will set the DEFAULT bin quantity (creates ADJUST movements).",
    )


def _normalize_header(h: str) -> str:
    """
    Normalize CSV header keys so different exports still work.
    Example: 'Starting Qty' -> 'starting_qty'
    """
    if h is None:
        return ""
    h = str(h).strip().lower()
    h = h.replace("\ufeff", "")  # BOM just in case
    h = h.replace(" ", "_")
    h = h.replace("-", "_")
    h = h.replace("/", "_")
    h = h.replace("__", "_")
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
    """
    Convert value to int safely.
    Handles: "10", "10.0", "1,234", "Qty: 5", etc.
    """
    if val is None:
        return default
    s = str(val).strip()
    if not s:
        return default

    # remove commas
    s = s.replace(",", "")

    # pull the first number we can find (supports negative if needed)
    m = re.search(r"-?\d+(\.\d+)?", s)
    if not m:
        return default

    try:
        return int(float(m.group(0)))
    except (ValueError, TypeError):
        return default


def _get_default_bin():
    """
    Ensures a DEFAULT bin exists for imports/adjustments.
    """
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
    """
    Safely reads an uploaded Django InMemoryUploadedFile/TemporaryUploadedFile
    and returns decoded text.
    Handles UTF-8 BOM and falls back to latin-1.
    """
    raw = file_obj.read()

    # Some CSVs can contain null bytes; strip them.
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.replace(b"\x00", b"")

    try:
        return raw.decode("utf-8-sig")
    except Exception:
        return raw.decode("latin-1", errors="replace")


def _find_qty(row: dict) -> int:
    """
    Supports many possible quantity column names (template + eBay exports + common variants).
    Row keys are assumed to already be normalized.
    """
    # First: direct known names
    candidates = [
        "starting_qty",
        "starting_quantity",
        "qty",
        "quantity",
        "available",
        "available_qty",
        "available_quantity",
        "qty_available",
        "quantity_available",
        "available_to_sell",
        "qty_available_to_sell",
        "quantity_available_to_sell",
        "quantity_available_for_sale",
        "available_for_sale",
        "on_hand",
        "on_hand_qty",
        "stock",
        "stock_qty",
        "inventory",
        "inventory_qty",
    ]

    for key in candidates:
        if key in row and str(row.get(key, "")).strip() != "":
            return _to_int(row.get(key), default=0)

    # Second: fuzzy matching for weird headers (like ebay reports)
    # If a column name contains both "avail" and "qty" or contains "quantity" and ("avail" or "sell")
    for k in row.keys():
        if not k:
            continue
        kk = str(k)
        val = str(row.get(k, "")).strip()
        if not val:
            continue

        if ("qty" in kk and "avail" in kk) or ("quantity" in kk and ("avail" in kk or "sell" in kk)):
            return _to_int(val, default=0)

    return 0


@transaction.atomic
def import_items_from_csv(file_obj, set_quantities: bool, user=None):
    """
    Imports Items from CSV.

    Required column:
      - sku

    Optional columns:
      - name, price, condition, description, image_url, listing_url, source, location
      - starting_qty (or many qty variants)

    Behavior:
      - Upserts Item by sku
      - If set_quantities=True:
          sets DEFAULT bin qty to provided quantity using ADJUST movements
    """
    created = 0
    updated = 0
    errors = []

    text = _read_uploaded_file_to_text(file_obj)

    # Use StringIO so csv module handles newlines correctly across platforms
    buf = io.StringIO(text)
    reader = csv.DictReader(buf)

    if not reader.fieldnames:
        return {"created": 0, "updated": 0, "errors": ["CSV has no header row."]}

    # Normalize headers
    reader.fieldnames = [_normalize_header(h) for h in reader.fieldnames]

    # Make sure we have a sku column
    if "sku" not in reader.fieldnames:
        return {
            "created": 0,
            "updated": 0,
            "errors": [f"Missing required column: sku. Found columns: {reader.fieldnames}"],
        }

    default_bin = _get_default_bin() if set_quantities else None

    # Start on line 2 because line 1 is the header
    for idx, row in enumerate(reader, start=2):
        try:
            # Normalize row keys and values
            clean_row = {}
            for k, v in (row or {}).items():
                nk = _normalize_header(k)
                nv = "" if v is None else str(v).strip()
                clean_row[nk] = nv

            sku = clean_row.get("sku", "").strip()
            if not sku:
                continue  # skip blank lines

            name = clean_row.get("name", "").strip() or sku
            price = _to_decimal(clean_row.get("price"), default=Decimal("0.00"))

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

            obj, was_created = Item.objects.update_or_create(
                sku=sku,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

            if set_quantities:
                target_qty = max(0, _find_qty(clean_row))

                bal, _ = InventoryBalance.objects.get_or_create(
                    item=obj,
                    bin=default_bin,
                    defaults={"quantity": 0},
                )
                current_qty = int(bal.quantity or 0)

                delta = target_qty - current_qty
                if delta != 0:
                    performed_by = None
                    if user and getattr(user, "is_authenticated", False):
                        performed_by = user

                    if delta > 0:
                        InventoryMovement.objects.create(
                            item=obj,
                            from_bin=None,
                            to_bin=default_bin,
                            movement_type="ADJUST",
                            quantity=delta,
                            note="CSV import set quantity",
                            performed_by=performed_by,
                        )
                    else:
                        InventoryMovement.objects.create(
                            item=obj,
                            from_bin=default_bin,
                            to_bin=None,
                            movement_type="ADJUST",
                            quantity=(-delta),
                            note="CSV import set quantity",
                            performed_by=performed_by,
                        )

                    # Ensure balance matches target even if movement logic changes later
                    bal.refresh_from_db()
                    if int(bal.quantity or 0) != target_qty:
                        InventoryBalance.objects.filter(pk=bal.pk).update(quantity=target_qty)

        except Exception as e:
            errors.append(f"Line {idx}: {e}")

    return {"created": created, "updated": updated, "errors": errors}

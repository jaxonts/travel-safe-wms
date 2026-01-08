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
        initial=True,  # default ON
        help_text="If checked, quantity column will set the DEFAULT bin quantity (creates ADJUST movements).",
    )


def _normalize_header(h: str) -> str:
    if h is None:
        return ""
    h = str(h).strip().lower()
    h = h.replace("\ufeff", "")  # BOM
    h = h.replace(" ", "_").replace("-", "_")
    # collapse repeated underscores
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

    # remove commas and stray currency symbols just in case
    s = s.replace(",", "").replace("$", "")

    # if it's something like "10.0" or "10.00"
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
        raw = raw.replace(b"\x00", b"")  # strip null bytes

    try:
        return raw.decode("utf-8-sig")
    except Exception:
        return raw.decode("latin-1", errors="replace")


def _find_qty(row: dict) -> int:
    """
    Supports many possible column names so your template/employee sheet works
    no matter how they label it.
    """
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


@transaction.atomic
def import_items_from_csv(file_obj, set_quantities: bool, user=None):
    created = 0
    updated = 0
    errors = []

    text = _read_uploaded_file_to_text(file_obj)
    buf = io.StringIO(text)
    reader = csv.DictReader(buf)

    if not reader.fieldnames:
        return {"created": 0, "updated": 0, "errors": ["CSV has no header row."]}

    # Normalize headers
    reader.fieldnames = [_normalize_header(h) for h in reader.fieldnames]

    if "sku" not in reader.fieldnames:
        return {
            "created": 0,
            "updated": 0,
            "errors": [f"Missing required column: sku. Found columns: {reader.fieldnames}"],
        }

    default_bin = _get_default_bin() if set_quantities else None
    performed_by = user if (user and getattr(user, "is_authenticated", False)) else None

    for idx, row in enumerate(reader, start=2):
        try:
            clean_row = {}
            for k, v in (row or {}).items():
                nk = _normalize_header(k)
                nv = "" if v is None else str(v).strip()
                clean_row[nk] = nv

            sku = clean_row.get("sku", "").strip()
            if not sku:
                continue

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

            obj, was_created = Item.objects.update_or_create(sku=sku, defaults=defaults)

            if was_created:
                created += 1
            else:
                updated += 1

            # ---- quantities ----
            if set_quantities:
                target_qty = max(0, _find_qty(clean_row))

                bal, _ = InventoryBalance.objects.get_or_create(
                    item=obj,
                    bin=default_bin,
                    defaults={"quantity": 0},
                )
                current_qty = int(bal.quantity or 0)
                delta = target_qty - current_qty

                # Always keep audit trail with ADJUST movement if different
                if delta != 0:
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

                # ✅ HARD SET the balance to the target (do not rely on movement save logic)
                InventoryBalance.objects.filter(pk=bal.pk).update(quantity=target_qty)

        except Exception as e:
            errors.append(f"Line {idx}: {e}")

    return {"created": created, "updated": updated, "errors": errors}

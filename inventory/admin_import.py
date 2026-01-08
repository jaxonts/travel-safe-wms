import csv
import io
from decimal import Decimal, InvalidOperation

from django import forms
from django.db import transaction

from .models import Item, Source, Bin, InventoryBalance, InventoryMovement


class ItemCSVImportForm(forms.Form):
    csv_file = forms.FileField()
    set_quantities = forms.BooleanField(
        required=False,
        initial=False,
        help_text="If checked, quantity column will set the DEFAULT bin quantity (and optionally create movements).",
    )


def _normalize_header(h: str) -> str:
    """
    Normalize CSV header keys so different exports still work.
    Example: 'Starting Quantity' -> 'starting_quantity'
    """
    if h is None:
        return ""
    h = str(h).strip().lower()
    h = h.replace("\ufeff", "")  # BOM
    h = h.replace(" ", "_")
    h = h.replace("-", "_")
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
    try:
        return int(float(s))
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
    Safely reads an uploaded Django file and returns decoded text.
    Handles UTF-8 BOM and falls back to latin-1.
    """
    # make sure we read from the start
    try:
        file_obj.seek(0)
    except Exception:
        pass

    raw = file_obj.read()

    # Strip null bytes just in case
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.replace(b"\x00", b"")

    try:
        return raw.decode("utf-8-sig")
    except Exception:
        return raw.decode("latin-1", errors="replace")


def _find_qty(row: dict) -> int:
    """
    Supports multiple possible quantity column names.
    Your CSV has: 'Starting Quantity' -> normalized to 'starting_quantity'
    """
    for key in (
        "starting_qty",
        "starting_quantity",
        "qty",
        "quantity",
        "on_hand",
        "onhand",
        "stock",
    ):
        if key in row and str(row.get(key, "")).strip() != "":
            return _to_int(row.get(key), default=0)
    return 0


def _supports_adjust() -> bool:
    """
    Returns True if InventoryMovement allows movement_type='ADJUST'
    (choices contain ADJUST).
    """
    try:
        choices = InventoryMovement._meta.get_field("movement_type").choices or []
        return any(c[0] == "ADJUST" for c in choices)
    except Exception:
        return False


@transaction.atomic
def import_items_from_csv(file_obj, set_quantities: bool, user=None):
    """
    Imports Items from CSV.

    Required:
      - sku

    Optional:
      - name, price, condition, description, image_url, listing_url, source, location
      - starting_quantity (or starting_qty/qty/quantity)

    Behavior:
      - Upserts Item by sku
      - If set_quantities=True:
          sets DEFAULT bin qty to provided quantity
          (creates ADJUST movements only if ADJUST is supported)
    """
    created = 0
    updated = 0
    errors = []
    warnings = []

    text = _read_uploaded_file_to_text(file_obj)

    buf = io.StringIO(text)
    reader = csv.DictReader(buf)

    if not reader.fieldnames:
        return {"created": 0, "updated": 0, "errors": ["CSV has no header row."], "warnings": []}

    # Normalize headers
    reader.fieldnames = [_normalize_header(h) for h in reader.fieldnames]

    if "sku" not in reader.fieldnames:
        return {
            "created": 0,
            "updated": 0,
            "errors": [f"Missing required column: sku. Found columns: {reader.fieldnames}"],
            "warnings": [],
        }

    default_bin = _get_default_bin() if set_quantities else None
    can_adjust = _supports_adjust()
    if set_quantities and not can_adjust:
        warnings.append(
            "Your InventoryMovement model does not support movement_type='ADJUST' on this server. "
            "Quantities will still be set correctly, but no ADJUST history entries will be created."
        )

    performed_by = None
    if user and getattr(user, "is_authenticated", False):
        performed_by = user

    # Start at line 2 because line 1 is header
    for idx, row in enumerate(reader, start=2):
        try:
            # Normalize row keys + values
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

                # Always set the balance directly (this is the key fix)
                if current_qty != target_qty:
                    InventoryBalance.objects.filter(pk=bal.pk).update(quantity=target_qty)

                # Optionally create movement history (only if ADJUST exists)
                delta = target_qty - current_qty
                if delta != 0 and can_adjust:
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

        except Exception as e:
            errors.append(f"Line {idx}: {e}")

    return {"created": created, "updated": updated, "errors": errors, "warnings": warnings}

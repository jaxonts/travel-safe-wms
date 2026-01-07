import csv
from io import StringIO

from django import forms
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.text import slugify

from .models import Item, Source, Bin, InventoryBalance, InventoryMovement


TEMPLATE_COLUMNS = [
    "sku",
    "name",
    "price",
    "condition",
    "description",
    "image_url",
    "listing_url",
    "source",
    "starting_qty",
]


class ItemCSVImportForm(forms.Form):
    csv_file = forms.FileField()
    set_quantities = forms.BooleanField(
        required=False,
        initial=False,
        help_text="If checked, will set starting_qty into DEFAULT bin using ADJUST movements.",
    )


def download_item_template_csv():
    """
    Returns an HttpResponse containing the template CSV.
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="wms_items_template.csv"'
    writer = csv.writer(response)
    writer.writerow(TEMPLATE_COLUMNS)
    # Example row:
    writer.writerow(
        [
            "SKU-001",
            "Example Item Name",
            "19.99",
            "New",
            "Optional description",
            "https://example.com/image.jpg",
            "https://www.ebay.com/itm/1234567890",
            "Manual",
            "10",
        ]
    )
    return response


def parse_decimal(value):
    try:
        if value is None:
            return None
        s = str(value).strip().replace("$", "").replace(",", "")
        if not s:
            return None
        return s  # let Django DecimalField parse it on assignment
    except Exception:
        return None


def parse_int(value, default=0):
    try:
        if value is None:
            return default
        s = str(value).strip()
        if not s:
            return default
        return int(float(s))
    except Exception:
        return default


def import_items_from_csv(file, set_quantities: bool, request=None):
    """
    Reads CSV and upserts Items.
    If set_quantities=True, uses starting_qty to create ADJUST InventoryMovements into DEFAULT bin.
    Returns (created_count, updated_count, errors_list).
    """
    # Ensure DEFAULT bin exists
    src, _ = Source.objects.get_or_create(name="Main Facility", defaults={"is_main_facility": True})
    default_bin, _ = Bin.objects.get_or_create(code="DEFAULT", defaults={"location": src})

    data = file.read()
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(StringIO(text))

    # Validate headers
    headers = set(reader.fieldnames or [])
    missing = set(TEMPLATE_COLUMNS) - headers
    if missing:
        return 0, 0, [f"CSV missing columns: {sorted(missing)}"]

    created = 0
    updated = 0
    errors = []

    row_num = 1  # header is row 1
    for row in reader:
        row_num += 1
        sku = (row.get("sku") or "").strip()
        name = (row.get("name") or "").strip()

        if not sku:
            errors.append(f"Row {row_num}: sku is required")
            continue

        defaults = {
            "name": name or sku,
            "price": parse_decimal(row.get("price")) or "0.00",
            "condition": (row.get("condition") or "").strip(),
            "description": (row.get("description") or "").strip(),
            "image_url": (row.get("image_url") or "").strip(),
            "listing_url": (row.get("listing_url") or "").strip(),
            "source": (row.get("source") or "Manual").strip() or "Manual",
            "location": "",  # keep blank; bin locations are handled via balances/bins
        }

        obj = Item.objects.filter(sku=sku).first()
        if obj is None:
            obj = Item(sku=sku, **defaults)
            try:
                obj.full_clean()
                obj.save()
                created += 1
            except Exception as e:
                errors.append(f"Row {row_num} (SKU {sku}): {e}")
                continue
        else:
            changed = False
            for k, v in defaults.items():
                if getattr(obj, k) != v:
                    setattr(obj, k, v)
                    changed = True
            try:
                if changed:
                    obj.full_clean()
                    obj.save(update_fields=list(defaults.keys()))
                updated += 1
            except Exception as e:
                errors.append(f"Row {row_num} (SKU {sku}): {e}")
                continue

        if set_quantities:
            desired_qty = parse_int(row.get("starting_qty"), default=0)

            bal, _ = InventoryBalance.objects.get_or_create(item=obj, bin=default_bin, defaults={"quantity": 0})
            current_qty = int(bal.quantity)
            diff = desired_qty - current_qty

            if diff != 0:
                # Increase => to_bin, Decrease => from_bin
                if diff > 0:
                    InventoryMovement.objects.create(
                        item=obj,
                        movement_type="ADJUST",
                        quantity=diff,
                        to_bin=default_bin,
                        performed_by=getattr(request, "user", None) if request and request.user.is_authenticated else None,
                        note=f"CSV import set qty to {desired_qty} (was {current_qty})",
                    )
                else:
                    InventoryMovement.objects.create(
                        item=obj,
                        movement_type="ADJUST",
                        quantity=abs(diff),
                        from_bin=default_bin,
                        performed_by=getattr(request, "user", None) if request and request.user.is_authenticated else None,
                        note=f"CSV import set qty to {desired_qty} (was {current_qty})",
                    )

    return created, updated, errors


def item_import_view(request):
    """
    Admin view page: download template + upload CSV import.
    """
    if request.method == "POST":
        form = ItemCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]
            set_quantities = form.cleaned_data["set_quantities"]

            created, updated, errors = import_items_from_csv(csv_file, set_quantities, request=request)

            if errors:
                messages.warning(request, f"Imported with {len(errors)} issue(s). Showing first 10.")
                for e in errors[:10]:
                    messages.error(request, e)

            messages.success(request, f"Import complete. Created: {created}, Updated: {updated}")
            return redirect("..")
    else:
        form = ItemCSVImportForm()

    return render(request, "admin/item_csv_import.html", {"form": form})


def item_template_view(request):
    return download_item_template_csv()


def get_item_import_urls(admin_site):
    """
    Returns URL patterns to be injected into ItemAdmin.get_urls().
    """
    return [
        path(
            "import-csv/",
            admin_site.admin_view(item_import_view),
            name="inventory_item_import_csv",
        ),
        path(
            "import-template/",
            admin_site.admin_view(item_template_view),
            name="inventory_item_import_template",
        ),
    ]

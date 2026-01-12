from django.contrib import admin, messages
from django.http import HttpResponse
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
import csv

from .models import Item, InventoryMovement, Bin, Source, InventoryBalance

# CSV import helper
from .admin_import import ItemCSVImportForm, import_items_from_csv


# ----------------------------
# Optional: ReportLab (Barcodes)
# ----------------------------
# If reportlab isn't installed, Django shouldn't crash.
REPORTLAB_OK = True
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.graphics.barcode import code128
except Exception:
    REPORTLAB_OK = False


# ----------------------------
# PDF Barcode Helpers
# ----------------------------

def _barcode_pdf_response(filename: str) -> HttpResponse:
    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


def _draw_label_page(c, title: str, value: str, subtitle: str = ""):
    """
    One label per page (simple, reliable for printing).
    """
    width, height = letter

    # Margins
    x = 0.75 * inch
    top = height - 0.9 * inch

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, top, (title or "")[:60])

    # Subtitle
    if subtitle:
        c.setFont("Helvetica", 10)
        c.drawString(x, top - 0.25 * inch, subtitle)

    # Barcode (Code128 handles letters + numbers, great for SKUs)
    barcode_val = (value or "").strip()
    b = code128.Code128(barcode_val, barHeight=0.9 * inch, barWidth=0.015 * inch)

    bx = x
    by = top - 1.5 * inch
    b.drawOn(c, bx, by)

    # Human-readable text
    c.setFont("Helvetica", 12)
    c.drawString(x, by - 0.25 * inch, barcode_val)

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(x, 0.6 * inch, "Tip: scan this, then scan a BIN barcode to assign/move.")


def build_labels_pdf(items):
    """
    items: list of dicts with {title, value, subtitle, filename}
    Returns HttpResponse PDF.
    """
    if not REPORTLAB_OK:
        return HttpResponse(
            "Barcode printing requires reportlab. Install it and redeploy.",
            status=500,
            content_type="text/plain",
        )

    filename = items[0].get("filename", "labels.pdf") if items else "labels.pdf"
    resp = _barcode_pdf_response(filename)
    c = canvas.Canvas(resp, pagesize=letter)

    for it in items:
        _draw_label_page(
            c,
            title=it.get("title", ""),
            value=it.get("value", ""),
            subtitle=it.get("subtitle", ""),
        )
        c.showPage()

    c.save()
    return resp


# ----------------------------
# Inline: Balances on Item page
# ----------------------------

class InventoryBalanceInline(admin.TabularInline):
    model = InventoryBalance
    extra = 0
    autocomplete_fields = ["bin"]
    fields = ("bin", "quantity")
    ordering = ("bin__location__name", "bin__code")


# ----------------------------
# Item Admin
# ----------------------------

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """
    ✅ Shows bin location based on InventoryBalance (authoritative).
    ✅ Lets you edit balances inline (manual quantity adjustment).
    ✅ Generates ADJUST movements automatically when balances change.
    ✅ Keeps barcode + CSV import/export.
    """
    list_display = (
        "sku",
        "name",
        "total_qty",
        "bin_location_display",
        "price",
        "location",
        "source",
    )
    search_fields = ("sku", "name", "location", "source")
    list_filter = ("source",)
    actions = ["export_to_csv", "print_item_barcodes_pdf"]

    inlines = [InventoryBalanceInline]

    # Import CSV link template
    change_list_template = "admin/item_changelist_with_import.html"

    def get_queryset(self, request):
        """
        ✅ Prevent N+1 queries in list view.
        """
        qs = super().get_queryset(request)
        return qs.prefetch_related("balances", "balances__bin", "balances__bin__location")

    def total_qty(self, obj):
        return obj.balances.aggregate(total=Sum("quantity"))["total"] or 0
    total_qty.short_description = "Quantity"

    def _primary_bin_for_item(self, obj):
        """
        Returns the first bin where qty > 0, sorted consistently.
        If later you want to show ALL bins, we can change this.
        """
        return (
            obj.balances
            .select_related("bin", "bin__location")
            .filter(quantity__gt=0)
            .order_by("bin__location__name", "bin__code")
            .first()
        )

    def bin_location_display(self, obj):
        bal = self._primary_bin_for_item(obj)
        return str(bal.bin) if bal else "-"
    bin_location_display.short_description = "Bin"

    @admin.action(description="Export selected items to CSV")
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="items_export.csv"'

        writer = csv.writer(response)
        writer.writerow(["SKU", "Name", "Total Quantity", "Bin", "Price", "Location", "Source"])

        # totals per item (fast)
        totals = (
            InventoryBalance.objects.filter(item__in=queryset)
            .values("item_id")
            .annotate(total=Sum("quantity"))
        )
        totals_map = {row["item_id"]: row["total"] for row in totals}

        # primary bin per item (first bin with qty>0)
        primary_bins = (
            InventoryBalance.objects
            .filter(item__in=queryset, quantity__gt=0)
            .select_related("bin", "bin__location")
            .order_by("item_id", "bin__location__name", "bin__code")
        )
        primary_bin_map = {}
        for bal in primary_bins:
            if bal.item_id not in primary_bin_map:
                primary_bin_map[bal.item_id] = str(bal.bin)

        for item in queryset:
            writer.writerow([
                item.sku,
                item.name,
                totals_map.get(item.id, 0),
                primary_bin_map.get(item.id, ""),
                item.price,
                item.location,
                item.source,
            ])

        return response

    @admin.action(description="Print barcode labels (PDF) for selected items")
    def print_item_barcodes_pdf(self, request, queryset):
        if not REPORTLAB_OK:
            self.message_user(request, "Barcode printing requires reportlab.", level=messages.ERROR)
            return None

        labels = []
        for obj in queryset.order_by("sku"):
            labels.append({
                "title": obj.name,
                "value": obj.sku,
                "subtitle": "ITEM SKU",
                "filename": "item-barcodes.pdf",
            })

        if not labels:
            self.message_user(request, "No items selected.", level=messages.WARNING)
            return None

        return build_labels_pdf(labels)

    # ✅ IMPORTANT: When balances are edited inline, create ADJUST movements.
    def save_formset(self, request, form, formset, change):
        if formset.model is InventoryBalance:
            instances = formset.save(commit=False)

            # deletes
            for obj in formset.deleted_objects:
                obj.delete()

            for inst in instances:
                item = inst.item

                # old qty from DB (authoritative)
                old_qty = 0
                if inst.pk:
                    old_qty = int(InventoryBalance.objects.get(pk=inst.pk).quantity or 0)

                new_qty = int(inst.quantity or 0)
                if new_qty < 0:
                    new_qty = 0

                delta = new_qty - old_qty

                # Save row (ensure it exists)
                inst.save()

                if delta != 0:
                    performed_by = request.user if getattr(request.user, "is_authenticated", False) else None

                    if delta > 0:
                        InventoryMovement.objects.create(
                            item=item,
                            from_bin=None,
                            to_bin=inst.bin,
                            movement_type="ADJUST",
                            quantity=delta,
                            note="Admin inline balance adjustment",
                            performed_by=performed_by,
                        )
                    else:
                        InventoryMovement.objects.create(
                            item=item,
                            from_bin=inst.bin,
                            to_bin=None,
                            movement_type="ADJUST",
                            quantity=(-delta),
                            note="Admin inline balance adjustment",
                            performed_by=performed_by,
                        )

                    # Force exact value as typed
                    InventoryBalance.objects.filter(pk=inst.pk).update(quantity=new_qty)

            formset.save_m2m()
            return

        super().save_formset(request, form, formset, change)

    # ---- Single-item barcode and import URLs ----
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/barcode/",
                self.admin_site.admin_view(self.item_barcode_view),
                name="inventory_item_barcode",
            ),
            path(
                "import-csv/",
                self.admin_site.admin_view(self.import_csv_view),
                name="inventory_item_import_csv",
            ),
            path(
                "import-template/",
                self.admin_site.admin_view(self.import_template_view),
                name="inventory_item_import_template",
            ),
        ]
        return custom + urls

    def item_barcode_view(self, request, object_id):
        if not REPORTLAB_OK:
            return HttpResponse("Barcode printing requires reportlab.", status=500)

        obj = self.get_object(request, object_id)
        if not obj:
            return HttpResponse("Item not found", status=404)

        labels = [{
            "title": obj.name,
            "value": obj.sku,
            "subtitle": "ITEM SKU",
            "filename": f"item-{obj.sku}-barcode.pdf",
        }]
        return build_labels_pdf(labels)

    # ---- CSV import views ----
    def import_csv_view(self, request):
        if request.method == "POST":
            form = ItemCSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                f = form.cleaned_data["csv_file"]
                set_qty = form.cleaned_data.get("set_quantities", False)

                result = import_items_from_csv(
                    file_obj=f,
                    set_quantities=set_qty,
                    user=request.user,
                )

                self.message_user(
                    request,
                    f"Import complete. Created: {result['created']}, Updated: {result['updated']}, Errors: {len(result['errors'])}",
                    level=messages.SUCCESS if not result["errors"] else messages.WARNING,
                )
                return TemplateResponse(
                    request,
                    "admin/item_csv_import.html",
                    {"form": form, "result": result},
                )
        else:
            form = ItemCSVImportForm()

        return TemplateResponse(request, "admin/item_csv_import.html", {"form": form})

    def import_template_view(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="items_import_template.csv"'
        writer = csv.writer(response)
        writer.writerow(
            ["sku", "name", "price", "condition", "description", "image_url", "listing_url", "source", "starting_qty"]
        )
        writer.writerow(["TSW000001", "Example Item", "19.99", "New", "Example description", "", "", "Manual", "0"])
        return response


# ----------------------------
# Inventory Balance Admin
# ----------------------------

@admin.register(InventoryBalance)
class InventoryBalanceAdmin(admin.ModelAdmin):
    list_display = ("item", "bin", "quantity")
    search_fields = ("item__sku", "item__name", "bin__code", "bin__location__name")
    list_filter = ("bin__location", "bin")


# ----------------------------
# Bin Admin (barcodes!)
# ----------------------------

@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ("code", "location")
    search_fields = ("code", "location__name")
    list_filter = ("location",)
    actions = ["print_bin_barcodes_pdf"]

    @admin.action(description="Print barcode labels (PDF) for selected bins")
    def print_bin_barcodes_pdf(self, request, queryset):
        if not REPORTLAB_OK:
            self.message_user(request, "Barcode printing requires reportlab.", level=messages.ERROR)
            return None

        labels = []
        for b in queryset.order_by("location__name", "code"):
            labels.append({
                "title": f"{b.location.name}",
                "value": b.code,
                "subtitle": "BIN",
                "filename": "bin-barcodes.pdf",
            })

        if not labels:
            self.message_user(request, "No bins selected.", level=messages.WARNING)
            return None

        return build_labels_pdf(labels)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/barcode/",
                self.admin_site.admin_view(self.bin_barcode_view),
                name="inventory_bin_barcode",
            ),
        ]
        return custom + urls

    def bin_barcode_view(self, request, object_id):
        if not REPORTLAB_OK:
            return HttpResponse("Barcode printing requires reportlab.", status=500)

        b = self.get_object(request, object_id)
        if not b:
            return HttpResponse("Bin not found", status=404)

        labels = [{
            "title": f"{b.location.name}",
            "value": b.code,
            "subtitle": "BIN",
            "filename": f"bin-{b.code}-barcode.pdf",
        }]
        return build_labels_pdf(labels)


# ----------------------------
# Source Admin
# ----------------------------

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "is_main_facility")
    search_fields = ("name",)


# ----------------------------
# Inventory Movement Admin
# ----------------------------

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = (
        "item_display",
        "movement_type",
        "quantity",
        "from_bin_display",
        "to_bin_display",
        "timestamp",
        "user_display",
    )
    list_filter = ("movement_type", "timestamp")
    search_fields = ("item__sku", "item__name")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("item", "from_bin", "to_bin", "performed_by", "from_bin__location", "to_bin__location")

    def item_display(self, obj):
        return obj.item.sku if obj.item_id else "Missing Item"
    item_display.short_description = "Item"

    def from_bin_display(self, obj):
        return str(obj.from_bin) if obj.from_bin else "-"
    from_bin_display.short_description = "From Bin"

    def to_bin_display(self, obj):
        return str(obj.to_bin) if obj.to_bin else "-"
    to_bin_display.short_description = "To Bin"

    def user_display(self, obj):
        return obj.performed_by.username if obj.performed_by else "-"
    user_display.short_description = "User"


# ----------------------------
# Unassigned Inventory View (balances)
# ----------------------------

class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "inventory/unassigned/",
                self.admin_view(self.unassigned_inventory_view),
                name="unassigned-inventory",
            ),
        ]
        return custom_urls + urls

    @staff_member_required
    def unassigned_inventory_view(self, request):
        items_qs = Item.objects.annotate(total=Sum("balances__quantity"))
        items = (items_qs.filter(total__isnull=True) | items_qs.filter(total=0))

        context = dict(
            self.each_context(request),
            items=items,
            title="Unassigned Inventory",
        )
        return TemplateResponse(request, "admin/unassigned_inventory.html", context)


custom_admin_site = CustomAdminSite(name="custom_admin")

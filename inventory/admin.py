from django.contrib import admin, messages
from django.http import HttpResponse
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
import csv

from .models import (
    Item,
    InventoryMovement,
    Bin,
    Source,
    InventoryBalance,
)

from .admin_import import (
    ItemCSVImportForm,
    import_items_from_csv,
)

REPORTLAB_OK = True

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.graphics.barcode import code128
except Exception:
    REPORTLAB_OK = False


# =========================================================
# LABEL SETTINGS
# =========================================================

LABEL_WIDTH = 50 * mm
LABEL_HEIGHT = 30 * mm


# =========================================================
# PDF HELPERS
# =========================================================

def _barcode_pdf_response(filename: str) -> HttpResponse:
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


def _centered_text(
    c,
    text,
    y,
    font_name="Helvetica",
    font_size=6,
):
    text = text or ""

    c.setFont(font_name, font_size)

    text_width = c.stringWidth(
        text,
        font_name,
        font_size,
    )

    x = (LABEL_WIDTH - text_width) / 2

    c.drawString(x, y, text)


def _draw_label_page(
    c,
    title: str,
    value: str,
    subtitle: str = "",
):
    barcode_val = (value or "").strip()

    title = (title or "")[:28]
    subtitle = (subtitle or "")[:18]

    _centered_text(
        c,
        title,
        LABEL_HEIGHT - 5 * mm,
        "Helvetica-Bold",
        5,
    )

    if subtitle:
        _centered_text(
            c,
            subtitle,
            LABEL_HEIGHT - 8 * mm,
            "Helvetica",
            4,
        )

    barcode = code128.Code128(
        barcode_val,
        barHeight=13 * mm,
        barWidth=0.42 * mm,
    )

    barcode_width = barcode.width

    bx = (LABEL_WIDTH - barcode_width) / 2
    by = 8 * mm

    barcode.drawOn(c, bx, by)

    _centered_text(
        c,
        barcode_val,
        4 * mm,
        "Helvetica",
        5,
    )


def build_labels_pdf(items):

    if not REPORTLAB_OK:
        return HttpResponse(
            "Barcode printing requires reportlab.",
            status=500,
            content_type="text/plain",
        )

    filename = (
        items[0].get("filename", "labels.pdf")
        if items
        else "labels.pdf"
    )

    response = _barcode_pdf_response(filename)

    c = canvas.Canvas(
        response,
        pagesize=(LABEL_WIDTH, LABEL_HEIGHT),
    )

    for item in items:

        _draw_label_page(
            c,
            title=item.get("title", ""),
            value=item.get("value", ""),
            subtitle=item.get("subtitle", ""),
        )

        c.showPage()

    c.save()

    return response


# =========================================================
# INLINE BALANCES
# =========================================================

class InventoryBalanceInline(admin.TabularInline):

    model = InventoryBalance

    extra = 0

    autocomplete_fields = ["bin"]

    fields = (
        "bin",
        "quantity",
    )

    ordering = (
        "bin__location__name",
        "bin__code",
    )


# =========================================================
# ITEM ADMIN
# =========================================================

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):

    list_display = (
        "sku",
        "name",
        "total_qty",
        "bin_location_display",
        "price",
        "location",
        "source",
    )

    search_fields = (
        "sku",
        "name",
        "location",
        "source",
    )

    actions = [
        "export_to_csv",
        "print_item_barcodes_pdf",
    ]

    inlines = [InventoryBalanceInline]

    change_list_template = (
        "admin/item_changelist_with_import.html"
    )

    list_per_page = 25
    show_full_result_count = False

    def get_queryset(self, request):

        qs = super().get_queryset(request)

        return (
            qs.annotate(
                total_quantity=Sum("balances__quantity")
            )
            .prefetch_related(
                "balances__bin",
                "balances__bin__location",
            )
        )

    def total_qty(self, obj):

        return obj.total_quantity or 0

    total_qty.short_description = "Quantity"

    def _primary_bin_for_item(self, obj):

        balances = list(obj.balances.all())

        positive_balances = [
            bal for bal in balances
            if bal.quantity and bal.quantity > 0 and bal.bin
        ]

        if not positive_balances:
            return None

        positive_balances.sort(
            key=lambda bal: (
                bal.bin.location.name
                if bal.bin.location
                else "",
                bal.bin.code or "",
            )
        )

        return positive_balances[0]

    def bin_location_display(self, obj):

        bal = self._primary_bin_for_item(obj)

        return str(bal.bin) if bal else "-"

    bin_location_display.short_description = "Bin"

    # =====================================================
    # EXPORT CSV
    # =====================================================

    @admin.action(description="Export selected items to CSV")
    def export_to_csv(self, request, queryset):

        response = HttpResponse(content_type="text/csv")

        response["Content-Disposition"] = (
            'attachment; filename="items_export.csv"'
        )

        writer = csv.writer(response)

        writer.writerow([
            "SKU",
            "Name",
            "Total Quantity",
            "Bin",
            "Price",
            "Location",
            "Source",
        ])

        totals = (
            InventoryBalance.objects
            .filter(item__in=queryset)
            .values("item_id")
            .annotate(total=Sum("quantity"))
        )

        totals_map = {
            row["item_id"]: row["total"]
            for row in totals
        }

        primary_bins = (
            InventoryBalance.objects
            .filter(
                item__in=queryset,
                quantity__gt=0,
            )
            .select_related(
                "bin",
                "bin__location",
            )
            .order_by(
                "item_id",
                "bin__location__name",
                "bin__code",
            )
        )

        primary_bin_map = {}

        for bal in primary_bins:

            if bal.item_id not in primary_bin_map:
                primary_bin_map[bal.item_id] = str(
                    bal.bin
                )

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

    # =====================================================
    # PRINT ITEM LABELS
    # =====================================================

    @admin.action(
        description="Print barcode labels (PDF) for selected items"
    )
    def print_item_barcodes_pdf(
        self,
        request,
        queryset,
    ):

        if not REPORTLAB_OK:

            self.message_user(
                request,
                "Barcode printing requires reportlab.",
                level=messages.ERROR,
            )

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

            self.message_user(
                request,
                "No items selected.",
                level=messages.WARNING,
            )

            return None

        return build_labels_pdf(labels)

    # =====================================================
    # URLS
    # =====================================================

    def get_urls(self):

        urls = super().get_urls()

        custom = [

            path(
                "<path:object_id>/barcode/",
                self.admin_site.admin_view(
                    self.item_barcode_view
                ),
                name="inventory_item_barcode",
            ),

            path(
                "<path:object_id>/change/barcode/",
                self.admin_site.admin_view(
                    self.item_barcode_view
                ),
                name="inventory_item_barcode_change",
            ),

            path(
                "import-csv/",
                self.admin_site.admin_view(
                    self.import_csv_view
                ),
                name="inventory_item_import_csv",
            ),

            path(
                "import-template/",
                self.admin_site.admin_view(
                    self.import_template_view
                ),
                name="inventory_item_import_template",
            ),
        ]

        return custom + urls

    # =====================================================
    # ITEM BARCODE VIEW
    # =====================================================

    def item_barcode_view(
        self,
        request,
        object_id,
    ):

        if not REPORTLAB_OK:

            return HttpResponse(
                "Barcode printing requires reportlab.",
                status=500,
            )

        obj = self.get_object(
            request,
            object_id,
        )

        if not obj:

            return HttpResponse(
                "Item not found",
                status=404,
            )

        labels = [{
            "title": obj.name,
            "value": obj.sku,
            "subtitle": "ITEM SKU",
            "filename": f"item-{obj.sku}-barcode.pdf",
        }]

        return build_labels_pdf(labels)

    # =====================================================
    # CSV IMPORT
    # =====================================================

    def import_csv_view(self, request):

        if request.method == "POST":

            form = ItemCSVImportForm(
                request.POST,
                request.FILES,
            )

            if form.is_valid():

                csv_file = form.cleaned_data["csv_file"]

                set_qty = form.cleaned_data.get(
                    "set_quantities",
                    False,
                )

                result = import_items_from_csv(
                    file_obj=csv_file,
                    set_quantities=set_qty,
                    user=request.user,
                )

                self.message_user(
                    request,
                    (
                        f"Import complete. "
                        f"Created: {result['created']}, "
                        f"Updated: {result['updated']}, "
                        f"Errors: {len(result['errors'])}"
                    ),
                    level=(
                        messages.SUCCESS
                        if not result["errors"]
                        else messages.WARNING
                    ),
                )

                return TemplateResponse(
                    request,
                    "admin/item_csv_import.html",
                    {
                        "form": form,
                        "result": result,
                    },
                )

        else:

            form = ItemCSVImportForm()

        return TemplateResponse(
            request,
            "admin/item_csv_import.html",
            {
                "form": form,
            },
        )

    # =====================================================
    # CSV TEMPLATE
    # =====================================================

    def import_template_view(self, request):

        response = HttpResponse(
            content_type="text/csv"
        )

        response["Content-Disposition"] = (
            'attachment; filename="items_import_template.csv"'
        )

        writer = csv.writer(response)

        writer.writerow([
            "sku",
            "name",
            "price",
            "condition",
            "description",
            "image_url",
            "listing_url",
            "source",
            "starting_qty",
        ])

        writer.writerow([
            "SKU-123",
            "Example Item",
            "19.99",
            "New",
            "Example description",
            "",
            "",
            "Manual",
            "0",
        ])

        return response


# =========================================================
# INVENTORY BALANCE ADMIN
# =========================================================

@admin.register(InventoryBalance)
class InventoryBalanceAdmin(admin.ModelAdmin):

    list_display = (
        "item",
        "bin",
        "quantity",
    )

    search_fields = (
        "item__sku",
        "item__name",
        "bin__code",
        "bin__location__name",
    )

    list_filter = (
        "bin__location",
        "bin",
    )

    list_per_page = 25
    show_full_result_count = False

    def get_queryset(self, request):

        qs = super().get_queryset(request)

        return qs.select_related(
            "item",
            "bin",
            "bin__location",
        )


# =========================================================
# BIN ADMIN
# =========================================================

@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "location",
    )

    search_fields = (
        "code",
        "location__name",
    )

    list_filter = ("location",)

    actions = ["print_bin_barcodes_pdf"]

    list_per_page = 25
    show_full_result_count = False

    def get_queryset(self, request):

        qs = super().get_queryset(request)

        return qs.select_related("location")

    @admin.action(
        description="Print barcode labels (PDF) for selected bins"
    )
    def print_bin_barcodes_pdf(
        self,
        request,
        queryset,
    ):

        if not REPORTLAB_OK:

            self.message_user(
                request,
                "Barcode printing requires reportlab.",
                level=messages.ERROR,
            )

            return None

        labels = []

        for b in queryset.order_by(
            "location__name",
            "code",
        ):

            labels.append({
                "title": f"{b.location.name}",
                "value": b.code,
                "subtitle": "BIN",
                "filename": "bin-barcodes.pdf",
            })

        if not labels:

            self.message_user(
                request,
                "No bins selected.",
                level=messages.WARNING,
            )

            return None

        return build_labels_pdf(labels)


# =========================================================
# SOURCE ADMIN
# =========================================================

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "address",
        "is_main_facility",
    )

    search_fields = ("name",)

    list_per_page = 25
    show_full_result_count = False


# =========================================================
# INVENTORY MOVEMENTS ADMIN
# =========================================================

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

    list_filter = (
        "movement_type",
        "timestamp",
    )

    search_fields = (
        "item__sku",
        "item__name",
    )

    list_per_page = 25
    show_full_result_count = False

    def get_queryset(self, request):

        qs = super().get_queryset(request)

        return qs.select_related(
            "item",
            "from_bin",
            "to_bin",
            "performed_by",
        )

    def item_display(self, obj):

        return (
            obj.item.sku
            if obj.item
            else "Missing Item"
        )

    item_display.short_description = "Item"

    def from_bin_display(self, obj):

        return (
            str(obj.from_bin)
            if obj.from_bin
            else "-"
        )

    from_bin_display.short_description = "From Bin"

    def to_bin_display(self, obj):

        return (
            str(obj.to_bin)
            if obj.to_bin
            else "-"
        )

    to_bin_display.short_description = "To Bin"

    def user_display(self, obj):

        return (
            obj.performed_by.username
            if obj.performed_by
            else "-"
        )

    user_display.short_description = "User"


# =========================================================
# CUSTOM ADMIN
# =========================================================

class CustomAdminSite(admin.AdminSite):

    def get_urls(self):

        urls = super().get_urls()

        custom_urls = [

            path(
                "inventory/unassigned/",
                self.admin_view(
                    self.unassigned_inventory_view
                ),
                name="unassigned-inventory",
            ),
        ]

        return custom_urls + urls

    @staff_member_required
    def unassigned_inventory_view(
        self,
        request,
    ):

        items_qs = Item.objects.annotate(
            total=Sum("balances__quantity")
        )

        items = (
            items_qs.filter(total__isnull=True)
            |
            items_qs.filter(total=0)
        )

        context = dict(
            self.each_context(request),
            items=items,
            title="Unassigned Inventory",
        )

        return TemplateResponse(
            request,
            "admin/unassigned_inventory.html",
            context,
        )


custom_admin_site = CustomAdminSite(
    name="custom_admin"
)
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Prefetch, Q, Sum
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import path

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


# ---------------------------------------------------------
# Optional ReportLab barcode support
# ---------------------------------------------------------

REPORTLAB_OK = True

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.graphics.barcode import code128
except Exception:
    REPORTLAB_OK = False


# ---------------------------------------------------------
# Barcode label dimensions
# 50 mm wide x 30 mm tall, landscape
# ---------------------------------------------------------

LABEL_WIDTH = 50 * mm
LABEL_HEIGHT = 30 * mm


# ---------------------------------------------------------
# Barcode PDF helpers
# ---------------------------------------------------------

def _barcode_value(value: str) -> str:
    """
    Clean a value before placing it into a barcode.

    If the value contains a # symbol, only the portion after
    the final # is used.
    """
    value = (value or "").strip()

    if "#" in value:
        return value.split("#")[-1].strip()

    return value


def _barcode_pdf_response(filename: str) -> HttpResponse:
    """
    Create an inline PDF response so the barcode opens
    in the browser's PDF viewer.
    """
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
    """
    Draw text horizontally centered on the label.
    """
    text = str(text or "")

    c.setFont(font_name, font_size)

    text_width = c.stringWidth(
        text,
        font_name,
        font_size,
    )

    x = (LABEL_WIDTH - text_width) / 2

    c.drawString(
        x,
        y,
        text,
    )


def _draw_label_page(
    c,
    title: str,
    value: str,
    subtitle: str = "",
):
    """
    Draw one 50 mm x 30 mm barcode label.
    """
    barcode_val = _barcode_value(value)

    if not barcode_val:
        barcode_val = "NO-SKU"

    # SKU/title above barcode
    _centered_text(
        c,
        barcode_val,
        LABEL_HEIGHT - 5 * mm,
        "Helvetica-Bold",
        6,
    )

    # Leave a small margin on both sides of the barcode.
    max_barcode_width = LABEL_WIDTH - (3 * mm)

    # Start with a larger bar width and reduce it only
    # when required to fit the label.
    bar_width = 0.50 * mm

    barcode = code128.Code128(
        barcode_val,
        barHeight=18 * mm,
        barWidth=bar_width,
    )

    while (
        barcode.width > max_barcode_width
        and bar_width > 0.28 * mm
    ):
        bar_width -= 0.02 * mm

        barcode = code128.Code128(
            barcode_val,
            barHeight=18 * mm,
            barWidth=bar_width,
        )

    # Center the barcode.
    barcode_x = (LABEL_WIDTH - barcode.width) / 2
    barcode_y = 5 * mm

    barcode.drawOn(
        c,
        barcode_x,
        barcode_y,
    )

    # Human-readable SKU below barcode.
    _centered_text(
        c,
        barcode_val,
        3.5 * mm,
        "Helvetica",
        4.5,
    )


def build_labels_pdf(items):
    """
    Create a PDF containing one barcode label per page.
    """
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

    pdf_canvas = canvas.Canvas(
        response,
        pagesize=(LABEL_WIDTH, LABEL_HEIGHT),
    )

    for item in items:
        _draw_label_page(
            pdf_canvas,
            title=item.get("title", ""),
            value=item.get("value", ""),
            subtitle=item.get("subtitle", ""),
        )

        pdf_canvas.showPage()

    pdf_canvas.save()

    return response


# ---------------------------------------------------------
# Inventory balance inline
# ---------------------------------------------------------

class InventoryBalanceInline(admin.TabularInline):
    model = InventoryBalance

    extra = 0

    autocomplete_fields = [
        "bin",
    ]

    fields = (
        "bin",
        "quantity",
    )

    ordering = (
        "bin__location__name",
        "bin__code",
    )

    show_change_link = True


# ---------------------------------------------------------
# Item admin
# ---------------------------------------------------------

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

    list_filter = (
        "source",
        "condition",
    )

    actions = [
        "export_to_csv",
        "print_item_barcodes_pdf",
    ]

    inlines = [
        InventoryBalanceInline,
    ]

    change_list_template = "admin/item_changelist_with_import.html"

    list_per_page = 25
    show_full_result_count = False
    preserve_filters = True

    ordering = (
        "sku",
    )

    def get_queryset(self, request):
        """
        Load the Item page efficiently.

        Quantity totals are calculated in the main query rather
        than running a separate aggregate query for every item.

        Inventory balances, bins, and bin locations are prefetched
        for the bin display column.
        """
        queryset = super().get_queryset(request)

        balance_queryset = (
            InventoryBalance.objects
            .select_related(
                "bin",
                "bin__location",
            )
            .order_by(
                "bin__location__name",
                "bin__code",
            )
        )

        return (
            queryset
            .select_related(
                "current_bin",
                "current_bin__location",
            )
            .annotate(
                calculated_total_qty=Sum(
                    "balances__quantity",
                ),
            )
            .prefetch_related(
                Prefetch(
                    "balances",
                    queryset=balance_queryset,
                    to_attr="prefetched_balances",
                ),
            )
        )

    @admin.display(
        description="Quantity",
        ordering="calculated_total_qty",
    )
    def total_qty(self, obj):
        """
        Return the total quantity already calculated by
        get_queryset().
        """
        return obj.calculated_total_qty or 0

    def _primary_bin_for_item(self, obj):
        """
        Find the first positive inventory balance using the balances
        that were already loaded by get_queryset().
        """
        balances = getattr(
            obj,
            "prefetched_balances",
            None,
        )

        if balances is None:
            balances = list(
                obj.balances
                .select_related(
                    "bin",
                    "bin__location",
                )
                .order_by(
                    "bin__location__name",
                    "bin__code",
                )
            )

        for balance in balances:
            if (
                balance.quantity
                and balance.quantity > 0
                and balance.bin_id
            ):
                return balance

        return None

    @admin.display(description="Bin")
    def bin_location_display(self, obj):
        """
        Display the first bin containing a positive quantity.
        """
        balance = self._primary_bin_for_item(obj)

        if not balance:
            return "-"

        return str(balance.bin)

    @admin.action(
        description="Export selected items to CSV",
    )
    def export_to_csv(self, request, queryset):
        """
        Export selected inventory items with total quantities
        and primary bins.
        """
        response = HttpResponse(
            content_type="text/csv",
        )

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

        selected_item_ids = list(
            queryset.values_list(
                "id",
                flat=True,
            )
        )

        totals = (
            InventoryBalance.objects
            .filter(
                item_id__in=selected_item_ids,
            )
            .values(
                "item_id",
            )
            .annotate(
                total=Sum("quantity"),
            )
        )

        totals_map = {
            row["item_id"]: row["total"]
            for row in totals
        }

        primary_bins = (
            InventoryBalance.objects
            .filter(
                item_id__in=selected_item_ids,
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

        for balance in primary_bins:
            if balance.item_id not in primary_bin_map:
                primary_bin_map[balance.item_id] = str(
                    balance.bin,
                )

        export_items = (
            Item.objects
            .filter(
                id__in=selected_item_ids,
            )
            .order_by(
                "sku",
            )
        )

        for item in export_items:
            writer.writerow([
                item.sku or "",
                item.name,
                totals_map.get(item.id, 0) or 0,
                primary_bin_map.get(item.id, ""),
                item.price,
                item.location,
                item.source,
            ])

        return response

    @admin.action(
        description="Print barcode labels (PDF) for selected items",
    )
    def print_item_barcodes_pdf(self, request, queryset):
        """
        Print one barcode label for every selected item.
        """
        if not REPORTLAB_OK:
            self.message_user(
                request,
                "Barcode printing requires reportlab.",
                level=messages.ERROR,
            )
            return None

        labels = []

        for obj in queryset.order_by("sku"):
            barcode_value = obj.sku or str(obj.pk)

            labels.append({
                "title": barcode_value,
                "value": barcode_value,
                "subtitle": "ITEM",
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

    def get_urls(self):
        """
        Add barcode and CSV import routes to the Item admin.
        """
        urls = super().get_urls()

        custom_urls = [
            path(
                "<path:object_id>/barcode/",
                self.admin_site.admin_view(
                    self.item_barcode_view,
                ),
                name="inventory_item_barcode",
            ),
            path(
                "<path:object_id>/change/barcode/",
                self.admin_site.admin_view(
                    self.item_barcode_view,
                ),
                name="inventory_item_barcode_change",
            ),
            path(
                "import-csv/",
                self.admin_site.admin_view(
                    self.import_csv_view,
                ),
                name="inventory_item_import_csv",
            ),
            path(
                "import-template/",
                self.admin_site.admin_view(
                    self.import_template_view,
                ),
                name="inventory_item_import_template",
            ),
        ]

        return custom_urls + urls

    def item_barcode_view(self, request, object_id):
        """
        Print a barcode for one individual item.
        """
        if not REPORTLAB_OK:
            return HttpResponse(
                "Barcode printing requires reportlab.",
                status=500,
                content_type="text/plain",
            )

        obj = self.get_object(
            request,
            object_id,
        )

        if obj is None:
            return HttpResponse(
                "Item not found.",
                status=404,
                content_type="text/plain",
            )

        barcode_value = obj.sku or str(obj.pk)

        labels = [{
            "title": barcode_value,
            "value": barcode_value,
            "subtitle": "ITEM",
            "filename": f"item-{barcode_value}-barcode.pdf",
        }]

        return build_labels_pdf(labels)

    def import_csv_view(self, request):
        """
        Display and process the inventory CSV import form.
        """
        result = None

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

                error_count = len(
                    result.get(
                        "errors",
                        [],
                    )
                )

                self.message_user(
                    request,
                    (
                        "Import complete. "
                        f"Created: {result.get('created', 0)}, "
                        f"Updated: {result.get('updated', 0)}, "
                        f"Errors: {error_count}"
                    ),
                    level=(
                        messages.SUCCESS
                        if error_count == 0
                        else messages.WARNING
                    ),
                )
        else:
            form = ItemCSVImportForm()

        context = {
            **self.admin_site.each_context(request),
            "form": form,
            "result": result,
            "title": "Import Inventory CSV",
            "opts": self.model._meta,
        }

        return TemplateResponse(
            request,
            "admin/item_csv_import.html",
            context,
        )

    def import_template_view(self, request):
        """
        Download a blank example inventory import template.
        """
        response = HttpResponse(
            content_type="text/csv",
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


# ---------------------------------------------------------
# Inventory balance admin
# ---------------------------------------------------------

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

    autocomplete_fields = (
        "item",
        "bin",
    )

    list_per_page = 25
    show_full_result_count = False
    preserve_filters = True

    def get_queryset(self, request):
        """
        Load the related Item, Bin, and Source in one query.
        """
        queryset = super().get_queryset(request)

        return queryset.select_related(
            "item",
            "bin",
            "bin__location",
        )


# ---------------------------------------------------------
# Bin admin
# ---------------------------------------------------------

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

    list_filter = (
        "location",
    )

    autocomplete_fields = (
        "location",
    )

    actions = [
        "print_bin_barcodes_pdf",
    ]

    list_per_page = 25
    show_full_result_count = False
    preserve_filters = True

    ordering = (
        "location__name",
        "code",
    )

    def get_queryset(self, request):
        """
        Load each bin's location in the same database query.
        """
        queryset = super().get_queryset(request)

        return queryset.select_related(
            "location",
        )

    @admin.action(
        description="Print barcode labels (PDF) for selected bins",
    )
    def print_bin_barcodes_pdf(self, request, queryset):
        """
        Print one barcode label for every selected bin.
        """
        if not REPORTLAB_OK:
            self.message_user(
                request,
                "Barcode printing requires reportlab.",
                level=messages.ERROR,
            )
            return None

        labels = []

        bins = (
            queryset
            .select_related(
                "location",
            )
            .order_by(
                "location__name",
                "code",
            )
        )

        for bin_obj in bins:
            labels.append({
                "title": bin_obj.code,
                "value": bin_obj.code,
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


# ---------------------------------------------------------
# Source admin
# ---------------------------------------------------------

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "address",
        "is_main_facility",
    )

    search_fields = (
        "name",
        "address",
    )

    list_filter = (
        "is_main_facility",
    )

    list_per_page = 25
    show_full_result_count = False
    preserve_filters = True

    ordering = (
        "name",
    )


# ---------------------------------------------------------
# Inventory movement admin
# ---------------------------------------------------------

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
        "from_bin__code",
        "to_bin__code",
    )

    autocomplete_fields = (
        "item",
        "from_bin",
        "to_bin",
        "performed_by",
    )

    readonly_fields = (
        "timestamp",
    )

    list_per_page = 25
    show_full_result_count = False
    preserve_filters = True

    date_hierarchy = "timestamp"

    ordering = (
        "-timestamp",
    )

    def get_queryset(self, request):
        """
        Load all movement-related objects in one query.

        The locations must also be selected because converting a Bin
        to text accesses bin.location.name.
        """
        queryset = super().get_queryset(request)

        return queryset.select_related(
            "item",
            "from_bin",
            "from_bin__location",
            "to_bin",
            "to_bin__location",
            "performed_by",
        )

    @admin.display(
        description="Item",
        ordering="item__sku",
    )
    def item_display(self, obj):
        if not obj.item_id:
            return "Missing Item"

        return obj.item.sku or str(obj.item_id)

    @admin.display(
        description="From Bin",
        ordering="from_bin__code",
    )
    def from_bin_display(self, obj):
        return str(obj.from_bin) if obj.from_bin else "-"

    @admin.display(
        description="To Bin",
        ordering="to_bin__code",
    )
    def to_bin_display(self, obj):
        return str(obj.to_bin) if obj.to_bin else "-"

    @admin.display(
        description="User",
        ordering="performed_by__username",
    )
    def user_display(self, obj):
        if not obj.performed_by_id:
            return "-"

        return obj.performed_by.username


# ---------------------------------------------------------
# Custom admin site
# ---------------------------------------------------------

class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "inventory/unassigned/",
                self.admin_view(
                    self.unassigned_inventory_view,
                ),
                name="unassigned-inventory",
            ),
        ]

        return custom_urls + urls

    @staff_member_required
    def unassigned_inventory_view(self, request):
        """
        Display items that have no inventory balance or a total
        quantity of zero.
        """
        items = (
            Item.objects
            .annotate(
                total=Sum(
                    "balances__quantity",
                ),
            )
            .filter(
                Q(total__isnull=True)
                | Q(total=0),
            )
            .select_related(
                "current_bin",
                "current_bin__location",
            )
            .order_by(
                "sku",
            )
        )

        context = {
            **self.each_context(request),
            "items": items,
            "title": "Unassigned Inventory",
        }

        return TemplateResponse(
            request,
            "admin/unassigned_inventory.html",
            context,
        )


custom_admin_site = CustomAdminSite(
    name="custom_admin",
)
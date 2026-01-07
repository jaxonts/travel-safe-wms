from django.contrib import admin
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

from .admin_import import get_item_import_urls


# =====================================================
# ITEM ADMIN (with CSV IMPORT + EXPORT)
# =====================================================

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "total_qty", "price", "location", "source")
    search_fields = ("sku", "name", "location", "source")
    actions = ["export_to_csv"]
    change_list_template = "admin/item_changelist_with_import.html"

    # Inject custom import URLs
    def get_urls(self):
        return get_item_import_urls(self.admin_site) + super().get_urls()

    def total_qty(self, obj):
        return obj.balances.aggregate(total=Sum("quantity"))["total"] or 0

    total_qty.short_description = "Quantity"

    @admin.action(description="Export selected items to CSV")
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="items_export.csv"'

        writer = csv.writer(response)
        writer.writerow(["SKU", "Name", "Total Quantity", "Price", "Location", "Source"])

        totals = (
            InventoryBalance.objects.filter(item__in=queryset)
            .values("item_id")
            .annotate(total=Sum("quantity"))
        )
        totals_map = {row["item_id"]: row["total"] for row in totals}

        for item in queryset:
            writer.writerow(
                [
                    item.sku,
                    item.name,
                    totals_map.get(item.id, 0),
                    item.price,
                    item.location,
                    item.source,
                ]
            )

        return response


# =====================================================
# INVENTORY BALANCES
# =====================================================

@admin.register(InventoryBalance)
class InventoryBalanceAdmin(admin.ModelAdmin):
    list_display = ("item", "bin", "quantity")
    search_fields = ("item__sku", "item__name", "bin__code", "bin__location__name")
    list_filter = ("bin__location", "bin")


# =====================================================
# BINS & SOURCES
# =====================================================

@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ("code", "location")
    search_fields = ("code", "location__name")
    list_filter = ("location",)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "is_main_facility")
    search_fields = ("name",)


# =====================================================
# INVENTORY MOVEMENTS
# =====================================================

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

    def item_display(self, obj):
        return obj.item.sku if obj.item else "Missing Item"

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


# =====================================================
# UNASSIGNED INVENTORY VIEW (BALANCE-BASED)
# =====================================================

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
        items = (
            Item.objects.annotate(total=Sum("balances__quantity"))
            .filter(total__isnull=True)
            | Item.objects.annotate(total=Sum("balances__quantity")).filter(total=0)
        )

        context = dict(
            self.each_context(request),
            items=items,
            title="Unassigned Inventory",
        )
        return TemplateResponse(request, "admin/unassigned_inventory.html", context)


custom_admin_site = CustomAdminSite(name="custom_admin")

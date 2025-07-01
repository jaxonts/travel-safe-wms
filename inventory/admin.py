from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.admin.views.decorators import staff_member_required
import csv

from .models import Item, InventoryMovement, Bin, Source

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'quantity', 'price', 'location', 'source', 'bin_display')
    search_fields = ('sku', 'name', 'location', 'source')
    actions = ['export_to_csv']  # ✅ CSV export action

    def bin_display(self, obj):
        return str(obj.bin) if obj.bin else "-"
    bin_display.short_description = 'Bin'

    @admin.action(description="Export selected items to CSV")
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="items_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['SKU', 'Name', 'Quantity', 'Price', 'Location', 'Source', 'Bin'])

        for item in queryset:
            writer.writerow([
                item.sku,
                item.name,
                item.quantity,
                item.price,
                item.location,
                item.source,
                item.bin.code if item.bin else ''
            ])

        return response

@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ('code', 'location')
    search_fields = ('code', 'location__name')

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'is_main_facility')
    search_fields = ('name',)

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = (
        'item_display', 'movement_type', 'quantity',
        'from_bin_display', 'to_bin_display', 'timestamp', 'user_display'
    )
    list_filter = ('movement_type', 'timestamp')
    search_fields = ('item__sku', 'item__name')

    def item_display(self, obj):
        return obj.item.sku if obj.item else "Missing Item"
    item_display.short_description = 'Item'

    def from_bin_display(self, obj):
        return str(obj.from_bin) if obj.from_bin else "-"
    from_bin_display.short_description = 'From Bin'

    def to_bin_display(self, obj):
        return str(obj.to_bin) if obj.to_bin else "-"
    to_bin_display.short_description = 'To Bin'

    def user_display(self, obj):
        return obj.performed_by.username if obj.performed_by else "-"
    user_display.short_description = 'User'

# ✅ Unassigned Inventory View
class CustomAdminSite(admin.AdminSite):

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("inventory/unassigned/", self.admin_view(self.unassigned_inventory_view), name="unassigned-inventory"),
        ]
        return custom_urls + urls

    @staff_member_required
    def unassigned_inventory_view(self, request):
        unassigned_items = Item.objects.filter(bin__isnull=True)
        context = dict(
            self.each_context(request),
            items=unassigned_items,
            title="Unassigned Inventory",
        )
        return TemplateResponse(request, "admin/unassigned_inventory.html", context)

custom_admin_site = CustomAdminSite(name='custom_admin')

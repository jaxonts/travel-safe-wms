from django.contrib import admin
from .models import Item, InventoryMovement, Bin, Source

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'quantity', 'price', 'location', 'source')
    search_fields = ('sku', 'name', 'location', 'source')

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
        return obj.user.username if obj.user else "-"
    user_display.short_description = 'User'

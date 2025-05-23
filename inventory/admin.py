from django.contrib import admin
from .models import Source, Bin, Item, InventoryMovement

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'is_main_facility')
    search_fields = ('name', 'address')
    list_filter = ('is_main_facility',)

@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ('code', 'location')
    search_fields = ('code',)
    list_filter = ('location',)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'quantity', 'bin')
    search_fields = ('name', 'sku')
    list_filter = ('bin',)

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('item', 'from_bin', 'to_bin', 'quantity', 'movement_type', 'timestamp', 'performed_by')
    search_fields = ('item__name', 'item__sku')
    list_filter = ('from_bin', 'to_bin', 'movement_type', 'timestamp', 'performed_by')

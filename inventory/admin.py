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

    @admin.display(description='Item')
    def item_display(self, obj):
        return obj.item.sku if obj.item else "Missing Item"

    @admin.display(description='From Bin')
    def from_bin_display(self, obj):
        return str(obj.from_bin) if obj.from_bin else "-"

    @admin.display(description='To Bin')
    def to_bin_display(self, obj):
        return str(obj.to_bin) if obj.to_bin else "-"

    @admin.display(description='User')
    def user_display(self, obj):
        # Only show if user attribute exists (prevents 500 errors)
        return getattr(obj.user, 'username', '-') if hasattr(obj, 'user') else "-"

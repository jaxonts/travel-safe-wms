from django.contrib import admin
from .models import Location, Bin, Item, InventoryMovement

admin.site.register(Location)
admin.site.register(Bin)
admin.site.register(Item)
admin.site.register(InventoryMovement)

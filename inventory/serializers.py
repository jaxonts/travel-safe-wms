from rest_framework import serializers
from .models import Location, Bin, Item, InventoryMovement

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class BinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bin
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class InventoryMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryMovement
        fields = '__all__'

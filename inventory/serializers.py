from rest_framework import serializers
from .models import Source, Bin, Item, InventoryMovement, InventoryBalance


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = "__all__"


class BinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bin
        fields = "__all__"


class ItemSerializer(serializers.ModelSerializer):
    # Helpful field for API consumers (dashboard) since quantity is no longer stored on Item
    total_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Item
        fields = "__all__"


class InventoryBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryBalance
        fields = "__all__"


class InventoryMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryMovement
        fields = "__all__"

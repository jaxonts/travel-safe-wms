from rest_framework import viewsets
from .models import Location, Bin, Item, InventoryMovement
from .serializers import LocationSerializer, BinSerializer, ItemSerializer, InventoryMovementSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class BinViewSet(viewsets.ModelViewSet):
    queryset = Bin.objects.all()
    serializer_class = BinSerializer

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

class InventoryMovementViewSet(viewsets.ModelViewSet):
    queryset = InventoryMovement.objects.all()
    serializer_class = InventoryMovementSerializer
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationViewSet, BinViewSet, ItemViewSet, InventoryMovementViewSet

router = DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'bins', BinViewSet)
router.register(r'items', ItemViewSet)
router.register(r'movements', InventoryMovementViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

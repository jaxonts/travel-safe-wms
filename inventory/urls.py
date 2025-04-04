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



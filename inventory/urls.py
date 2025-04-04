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
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('inventory.urls')),  # ✅ This line includes your API endpoints
]

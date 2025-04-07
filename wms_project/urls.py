from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# Views from inventory
from inventory.views import (
    LocationViewSet,
    BinViewSet,
    ItemViewSet,
    InventoryMovementViewSet,
    dashboard,
)

# DRF API router
router = DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'bins', BinViewSet)
router.register(r'items', ItemViewSet)
router.register(r'movements', InventoryMovementViewSet)

# URL patterns
urlpatterns = [
    path('', dashboard, name='dashboard'),                      # 👈 Homepage
    path('admin/', admin.site.urls),                            # Admin login & control
    path('api/', include(router.urls)),                         # API endpoints
    path('accounts/', include('django.contrib.auth.urls')),     # Login, logout, password reset
]

# Static file handling (only in development)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)




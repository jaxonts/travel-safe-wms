from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from inventory.views import LocationViewSet, BinViewSet, ItemViewSet, InventoryMovementViewSet
from django.shortcuts import redirect  # ✅ Optional: redirect to /admin if home is visited

# DRF API router
router = DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'bins', BinViewSet)
router.register(r'items', ItemViewSet)
router.register(r'movements', InventoryMovementViewSet)

urlpatterns = [
    path('', lambda request: redirect('/admin/')),  # ✅ Redirect base path to admin
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('accounts/', include('django.contrib.auth.urls')),  # Enables login/logout/password views
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

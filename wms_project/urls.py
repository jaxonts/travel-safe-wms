from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

# Views from inventory
from inventory.views import (
    LocationViewSet,
    BinViewSet,
    ItemViewSet,
    InventoryMovementViewSet,
    dashboard,  # Optional homepage view
)

# DRF API router
router = DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'bins', BinViewSet)
router.register(r'items', ItemViewSet)
router.register(r'movements', InventoryMovementViewSet)  # ✅ This was broken before

# URL patterns
urlpatterns = [
    path('', dashboard, name='dashboard'),  # Optional homepage view
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('accounts/', include('django.contrib.auth.urls')),

    # ✅ Custom dashboard for non-admin users
    path('dashboard/', login_required(TemplateView.as_view(template_name="dashboard.html")), name='user_dashboard'),
]

# Static file handling (only in development)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

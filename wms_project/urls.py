from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

# Inventory views
from inventory.views import (
    SourceViewSet,
    BinViewSet,
    ItemViewSet,
    InventoryMovementViewSet,
    dashboard,
    ebay_notifications,
    ebay_oauth_callback,
    ebay_active_inventory
)

# DRF Router Setup
router = DefaultRouter()
router.register(r'sources', SourceViewSet)
router.register(r'bins', BinViewSet)
router.register(r'items', ItemViewSet)
router.register(r'movements', InventoryMovementViewSet)

urlpatterns = [
    # Admin and Auth
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),

    # Dashboard
    path('', dashboard, name='dashboard'),
    path('dashboard/', login_required(TemplateView.as_view(template_name="dashboard.html")), name='user_dashboard'),

    # API
    path('api/', include(router.urls)),

    # eBay Integration
    path('api/ebay/webhook/', ebay_notifications, name='ebay_webhook'),              # Webhook verification
    path('auth/ebay/return/', ebay_oauth_callback, name='ebay_oauth_callback'),      # OAuth redirect
    path('api/ebay/inventory/', ebay_active_inventory, name='ebay_active_inventory') # Inventory sync
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

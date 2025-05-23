from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

# Import views from the inventory app
from inventory.views import (
    SourceViewSet,
    BinViewSet,
    ItemViewSet,
    InventoryMovementViewSet,
    dashboard,
    ebay_notifications,       # Webhook challenge handler
    ebay_oauth_callback,      # OAuth redirect handler
    ebay_active_inventory     # eBay inventory sync view
)

# Set up DRF API router
router = DefaultRouter()
router.register(r'sources', SourceViewSet)
router.register(r'bins', BinViewSet)
router.register(r'items', ItemViewSet)
router.register(r'movements', InventoryMovementViewSet)

# Define URL patterns
urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('accounts/', include('django.contrib.auth.urls')),
    path('dashboard/', login_required(TemplateView.as_view(template_name="dashboard.html")), name='user_dashboard'),

    # eBay integrations
    path('api/ebay/webhook/', ebay_notifications, name='ebay_webhook'),
    path('auth/ebay/return/', ebay_oauth_callback, name='ebay_oauth_callback'),
    path('api/ebay/inventory/', ebay_active_inventory, name='ebay_active_inventory'),
]

# Static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

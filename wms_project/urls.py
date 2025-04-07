from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# Import your views
from inventory.views import (
    LocationViewSet,
    BinViewSet,
    ItemViewSet,
    InventoryMovementViewSet,
    dashboard
)

router = DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'bins', BinViewSet)
router.register(r'items', ItemViewSet)
router.register(r'movements', InventoryMovementViewSet)

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('accounts/', include('django.contrib.auth.urls')),  # ✅ THIS IS NEEDED
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)




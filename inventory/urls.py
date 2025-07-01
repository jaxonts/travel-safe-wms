from django.urls import path
from . import views

urlpatterns = [
    path('unassigned-inventory/', views.unassigned_inventory_view, name='unassigned_inventory'),
]

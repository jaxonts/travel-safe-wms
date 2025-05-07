from rest_framework import viewsets
from .models import Source, Bin, Item, InventoryMovement
from .serializers import SourceSerializer, BinSerializer, ItemSerializer, InventoryMovementSerializer
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer

class BinViewSet(viewsets.ModelViewSet):
    queryset = Bin.objects.all()
    serializer_class = BinSerializer

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

class InventoryMovementViewSet(viewsets.ModelViewSet):
    queryset = InventoryMovement.objects.all()
    serializer_class = InventoryMovementSerializer

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@csrf_exempt
def ebay_notifications(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            challenge = payload.get("challenge")
            if challenge:
                return HttpResponse(challenge, status=200)
        except Exception:
            pass
    return HttpResponse(status=400)

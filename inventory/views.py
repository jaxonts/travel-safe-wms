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
    """
    Respond to eBay webhook challenge requests (both GET and POST).
    eBay expects a plain-text response with the exact verification token.
    """
    if request.method == "GET":
        challenge = request.GET.get("challenge")
        if challenge:
            return HttpResponse(challenge, content_type="text/plain")

    elif request.method == "POST":
        try:
            body = request.body.decode('utf-8')
            data = json.loads(body)
            challenge = data.get("challenge")
            if challenge:
                return HttpResponse(challenge, content_type="text/plain")
        except Exception as e:
            print(f"[eBay webhook error] {e}")

    return HttpResponse("Invalid", status=400)

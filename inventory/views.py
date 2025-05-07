from rest_framework import viewsets
from .models import Source, Bin, Item, InventoryMovement
from .serializers import SourceSerializer, BinSerializer, ItemSerializer, InventoryMovementSerializer
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import hashlib

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
    if request.method == 'GET':
        challenge_code = request.GET.get('challenge_code')
        if challenge_code:
            verification_token = 'TSW-Notify-Endpoint-Verification-Token-2025'  # ✅ Replace with your token
            endpoint = 'https://travel-safe-wms.onrender.com/ebay/notifications/'  # ✅ Must match eBay settings

            data_to_hash = challenge_code + verification_token + endpoint
            hashed = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()

            return JsonResponse({'challengeResponse': hashed})
    return HttpResponse("Invalid request", status=400)

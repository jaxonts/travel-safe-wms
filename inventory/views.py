from rest_framework import viewsets
from .models import Source, Bin, Item, InventoryMovement
from .serializers import SourceSerializer, BinSerializer, ItemSerializer, InventoryMovementSerializer
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
    # This handles eBay's account deletion verification ping
    challenge = request.GET.get('challenge')
    if challenge:
        return JsonResponse({"challengeResponse": challenge})
    return JsonResponse({"message": "OK"})

from rest_framework import viewsets
from .models import Source, Bin, Item, InventoryMovement
from .serializers import SourceSerializer, BinSerializer, ItemSerializer, InventoryMovementSerializer

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import json
import requests
import urllib.parse
import base64

# --------------------------
# WMS API Views
# --------------------------

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

    def perform_create(self, serializer):
        # Set from_bin automatically from the current bin location of the item
        item = serializer.validated_data['item']
        from_bin = item.bin

        # Save the InventoryMovement with from_bin
        movement = serializer.save(from_bin=from_bin)

        # Update the item's bin to the new location
        item.bin = movement.to_bin
        item.save()

# --------------------------
# Dashboard View
# --------------------------

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

# --------------------------
# eBay Webhook Challenge Handler
# --------------------------

@csrf_exempt
def ebay_notifications(request):
    if request.method == "GET":
        challenge = request.GET.get("challenge")
        if challenge:
            return HttpResponse(challenge, content_type="text/plain")
    elif request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            challenge = data.get("challenge")
            if challenge:
                return HttpResponse(challenge, content_type="text/plain")
        except Exception as e:
            print(f"[Webhook Error] {e}")

    return HttpResponse("Invalid", status=400)

# --------------------------
# eBay OAuth Redirect Handler
# --------------------------

@csrf_exempt
def ebay_oauth_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponse("❌ No authorization code received.", status=400)

    token_url = "https://api.ebay.com/identity/v1/oauth2/token"
    credentials = f"{settings.EBAY_CLIENT_ID}:{settings.EBAY_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}",
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.EBAY_REDIRECT_URI,
    }

    try:
        response = requests.post(token_url, headers=headers, data=urllib.parse.urlencode(data))
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({
                "error": "Token exchange failed",
                "status_code": response.status_code,
                "details": response.json()
            }, status=400)
    except Exception as e:
        return JsonResponse({
            "error": "Exception during token exchange",
            "message": str(e)
        }, status=500)

# --------------------------
# eBay Active Inventory Sync to WMS
# --------------------------

@csrf_exempt
def ebay_active_inventory(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    access_token = settings.EBAY_ACCESS_TOKEN
    url = "https://api.ebay.com/sell/inventory/v1/inventory_item"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return JsonResponse({
                "error": "Failed to fetch inventory",
                "status": response.status_code,
                "details": response.json()
            }, status=400)

        inventory = response.json()
        results = []

        for item in inventory.get("inventoryItems", []):
            title = item.get("product", {}).get("title", "N/A")
            sku = item.get("sku")
            if not sku:
                continue
            obj, created = Item.objects.update_or_create(
                sku=sku,
                defaults={"name": title}
            )
            results.append({
                "sku": sku,
                "name": title,
                "status": "created" if created else "updated"
            })

        return JsonResponse(results, safe=False)

    except Exception as e:
        return JsonResponse({
            "error": "Unexpected error occurred",
            "message": str(e)
        }, status=500)

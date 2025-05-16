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

# Inventory API views
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

# Dashboard
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

# eBay webhook challenge-response (for Marketplace Account Deletion)
@csrf_exempt
def ebay_notifications(request):
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

# eBay OAuth Redirect Handler
@csrf_exempt
def ebay_oauth_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponse("❌ No authorization code received.", status=400)

    token_url = "https://api.ebay.com/identity/v1/oauth2/token"

    # Base64 encode: client_id:client_secret
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

    response = requests.post(token_url, headers=headers, data=urllib.parse.urlencode(data))

    if response.status_code == 200:
        token_data = response.json()
        return JsonResponse(token_data)
    else:
        return JsonResponse(
            {"error": "Token exchange failed", "details": response.json()},
            status=400
        )

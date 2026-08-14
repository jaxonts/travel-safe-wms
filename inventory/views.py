from rest_framework import viewsets
from django.db.models import Sum

from .models import (
    Source,
    Bin,
    Item,
    InventoryMovement,
    InventoryBalance,
)
from .serializers import (
    SourceSerializer,
    BinSerializer,
    ItemSerializer,
    InventoryMovementSerializer,
    InventoryBalanceSerializer,
)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import json
import requests
import urllib.parse
import base64

# =====================================================
# WMS API VIEWS (REST)
# =====================================================

class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer


class BinViewSet(viewsets.ModelViewSet):
    queryset = Bin.objects.select_related("location").all()
    serializer_class = BinSerializer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class InventoryBalanceViewSet(viewsets.ModelViewSet):
    queryset = InventoryBalance.objects.select_related(
        "item", "bin", "bin__location"
    ).all()
    serializer_class = InventoryBalanceSerializer


class InventoryMovementViewSet(viewsets.ModelViewSet):
    queryset = InventoryMovement.objects.select_related(
        "item", "from_bin", "to_bin", "performed_by"
    ).all()
    serializer_class = InventoryMovementSerializer

    def perform_create(self, serializer):
        # IMPORTANT:
        # InventoryMovement.save() already updates InventoryBalance.
        # Do NOT mutate Item or infer bins here.
        serializer.save(
            performed_by=self.request.user
            if self.request.user.is_authenticated
            else None
        )

# =====================================================
# DASHBOARD VIEW
# =====================================================

@login_required
def dashboard(request):
    return render(request, "dashboard.html")

# =====================================================
# UNASSIGNED INVENTORY VIEW (ADMIN)
# =====================================================

@staff_member_required
def unassigned_inventory_view(request):
    # "Unassigned" = item has no inventory balances at all
    items = Item.objects.filter(balances__isnull=True).distinct()

    # Alternative definition (commented):
    # items = (
    #     Item.objects.annotate(total=Sum("balances__quantity"))
    #     .filter(total__isnull=True)
    #     | Item.objects.annotate(total=Sum("balances__quantity")).filter(total=0)
    # )

    return render(
        request,
        "admin/unassigned_inventory.html",
        {"items": items},
    )

# =====================================================
# EBAY WEBHOOK CHALLENGE HANDLER
# =====================================================

@csrf_exempt
def ebay_notifications(request):
    if request.method == "GET":
        challenge = request.GET.get("challenge")
        if challenge:
            return HttpResponse(challenge, content_type="text/plain")

    elif request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            challenge = data.get("challenge")
            if challenge:
                return HttpResponse(challenge, content_type="text/plain")
        except Exception as e:
            print(f"[Webhook Error] {e}")

    return HttpResponse("Invalid", status=400)

# =====================================================
# EBAY OAUTH CALLBACK
# =====================================================

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
        response = requests.post(
            token_url, headers=headers, data=urllib.parse.urlencode(data)
        )
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse(
                {
                    "error": "Token exchange failed",
                    "status_code": response.status_code,
                    "details": response.json(),
                },
                status=400,
            )
    except Exception as e:
        return JsonResponse(
            {
                "error": "Exception during token exchange",
                "message": str(e),
            },
            status=500,
        )

# =====================================================
# EBAY TOKEN REFRESH HELPER
# =====================================================

def refresh_ebay_token():
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {
        "Authorization": f"Basic {settings.EBAY_BASE64_ENCODED_CREDENTIALS}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": settings.EBAY_REFRESH_TOKEN,
        "scope": (
            "https://api.ebay.com/oauth/api_scope "
            "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly"
        ),
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

# =====================================================
# EBAY ACTIVE INVENTORY SYNC (CATALOG ONLY)
# =====================================================

@csrf_exempt
def ebay_active_inventory(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    access_token = refresh_ebay_token()
    if not access_token:
        return JsonResponse({"error": "Failed to refresh token"}, status=401)

    url = "https://api.ebay.com/sell/inventory/v1/inventory_item"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return JsonResponse(
                {
                    "error": "Failed to fetch inventory",
                    "status": response.status_code,
                    "details": response.json(),
                },
                status=400,
            )

        inventory = response.json()
        results = []

        for item in inventory.get("inventoryItems", []):
            title = item.get("product", {}).get("title", "N/A")
            sku = item.get("sku")
            if not sku:
                continue

            obj, created = Item.objects.update_or_create(
                sku=sku,
                defaults={"name": title},
            )

            results.append(
                {
                    "sku": sku,
                    "name": title,
                    "status": "created" if created else "updated",
                }
            )

        return JsonResponse(results, safe=False)

    except Exception as e:
        return JsonResponse(
            {
                "error": "Unexpected error occurred",
                "message": str(e),
            },
            status=500,
        )


# =====================================================
# DUPLICATE INVENTORY VIEW (ADMIN)
# =====================================================

@staff_member_required
def duplicate_inventory_view(request):
    """
    Review possible duplicate WMS items.

    Shows:
    1. Exact duplicate full SKUs
    2. Different SKUs that share the same value after the final #

    Nothing is automatically deleted or merged.
    """

    items = (
        Item.objects
        .all()
        .order_by("sku", "id")
    )

    exact_sku_map = {}
    suffix_map = {}

    for item in items:
        sku = (item.sku or "").strip()

        if not sku:
            continue

        # Exact full SKU grouping
        exact_sku_map.setdefault(sku, []).append(item)

        # Use stored suffix if available, otherwise calculate it
        suffix = (getattr(item, "sku_suffix", "") or "").strip()

        if not suffix and "#" in sku:
            suffix = sku.rsplit("#", 1)[1].strip()

        if suffix:
            suffix_map.setdefault(suffix, []).append(item)

    exact_sku_groups = []

    for sku, grouped_items in exact_sku_map.items():
        if len(grouped_items) > 1:
            exact_sku_groups.append({
                "value": sku,
                "items": grouped_items,
            })

    suffix_groups = []

    for suffix, grouped_items in suffix_map.items():
        if len(grouped_items) <= 1:
            continue

        unique_skus = {
            (item.sku or "").strip()
            for item in grouped_items
        }

        # If every SKU is identical, it is already shown in
        # the Exact Duplicate SKU section.
        if len(unique_skus) <= 1:
            continue

        suffix_groups.append({
            "value": suffix,
            "items": grouped_items,
        })

    exact_sku_groups.sort(
        key=lambda group: group["value"]
    )

    suffix_groups.sort(
        key=lambda group: group["value"]
    )

    return render(
        request,
        "admin/duplicate_inventory.html",
        {
            "exact_sku_groups": exact_sku_groups,
            "suffix_groups": suffix_groups,
            "exact_group_count": len(exact_sku_groups),
            "suffix_group_count": len(suffix_groups),
            "title": "Duplicate Inventory",
        },
    )

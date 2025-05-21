import os
import django
import requests
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wms_project.settings")
django.setup()

from django.conf import settings
from inventory.models import Item

print("🚨 models.py is being read!")

access_token = settings.EBAY_ACCESS_TOKEN
url = "https://api.ebay.com/sell/inventory/v1/inventory_item"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Content-Language": "en-US"
}

# Get all Item objects with a SKU and Name
items = Item.objects.exclude(sku__isnull=True).exclude(sku="").exclude(name__isnull=True).exclude(name="")

if not items.exists():
    print("✅ No eligible WMS items to push to eBay.")
    exit()

success_count = 0
failures = []

for item in items:
    payload = {
        "sku": item.sku,
        "product": {
            "title": item.name
        }
    }

    response = requests.put(
        f"{url}/{item.sku}",
        headers=headers,
        data=json.dumps(payload)
    )

    if response.status_code in [200, 201, 204]:
        print(f"✅ Uploaded item: {item.sku}")
        success_count += 1
    else:
        print(f"❌ Failed to upload {item.sku}: {response.status_code}")
        try:
            print(response.json())
            failures.append({item.sku: response.json()})
        except Exception:
            print("❌ Could not parse error")

print(f"\n✅ Finished. Successfully pushed {success_count} items.")
if failures:
    print(f"\n❌ {len(failures)} items failed to push.")

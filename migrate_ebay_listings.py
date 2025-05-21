import os
import requests
import json
from django.conf import settings
from django.core.wsgi import get_wsgi_application

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wms_project.settings")
application = get_wsgi_application()

from inventory.models import Item

def migrate_ebay_inventory_to_wms():
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
            print("❌ Failed to fetch inventory:", response.status_code)
            print(response.json())
            return

        inventory = response.json()
        items = inventory.get("inventoryItems", [])

        if not items:
            print("✅ No inventory items found to migrate.")
            return

        created_count = 0
        updated_count = 0

        for item in items:
            title = item.get("product", {}).get("title", "Untitled")
            sku = item.get("sku")

            if not sku:
                continue

            obj, created = Item.objects.update_or_create(
                sku=sku,
                defaults={"name": title}
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        print(f"✅ Done. Created: {created_count}, Updated: {updated_count}")

    except Exception as e:
        print("❌ Error during migration:", str(e))

if __name__ == "__main__":
    migrate_ebay_inventory_to_wms()

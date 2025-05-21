# inventory/management/commands/sync_ebay_inventory.py

from django.core.management.base import BaseCommand
from django.conf import settings
from inventory.models import Item

import requests

class Command(BaseCommand):
    help = 'Synchronize eBay listings with WMS'

    def handle(self, *args, **kwargs):
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
                self.stderr.write(self.style.ERROR(f"Failed to fetch inventory: {response.status_code}"))
                self.stderr.write(str(response.json()))
                return

            inventory = response.json()
            count = 0

            for item in inventory.get("inventoryItems", []):
                title = item.get("product", {}).get("title", "N/A")
                sku = item.get("sku")
                if not sku:
                    continue
                Item.objects.update_or_create(
                    sku=sku,
                    defaults={"name": title}
                )
                count += 1

            self.stdout.write(self.style.SUCCESS(f"Successfully synced {count} items from eBay."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error during sync: {str(e)}"))

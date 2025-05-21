from django.core.management.base import BaseCommand
from django.conf import settings
from inventory.models import Item
import requests

class Command(BaseCommand):
    help = "Sync active eBay listings into WMS"

    def handle(self, *args, **options):
        print("🚨 models.py is being read!")

        access_token = settings.EBAY_ACCESS_TOKEN
        url = "https://api.ebay.com/sell/inventory/v1/inventory_item"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                self.stderr.write(self.style.ERROR(f"❌ Failed to fetch listings: {response.status_code}"))
                self.stderr.write(str(response.json()))
                return

            data = response.json()
            items = data.get("inventoryItems", [])
            if not items:
                self.stdout.write("✅ No active listings found.")
                return

            created, updated = 0, 0
            for listing in items:
                sku = listing.get("sku")
                title = listing.get("product", {}).get("title", "No Title")

                if not sku:
                    continue

                obj, created_flag = Item.objects.update_or_create(
                    sku=sku,
                    defaults={"name": title}
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

            self.stdout.write(f"✅ Synced {created} new and {updated} updated eBay listings into WMS.")

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Sync error: {str(e)}"))

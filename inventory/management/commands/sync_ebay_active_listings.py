from django.core.management.base import BaseCommand
from django.conf import settings
from inventory.models import Item
from ebay.utils import refresh_ebay_access_token
import requests
import xml.etree.ElementTree as ET

class Command(BaseCommand):
    help = "Sync active eBay listings into WMS using Trading API"

    def handle(self, *args, **options):
        print("🚨 models.py is being read!")

        # Refresh access token
        access_token = refresh_ebay_access_token()

        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-CALL-NAME": "GetMyeBaySelling",
            "X-EBAY-API-SITEID": "0",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-IAF-TOKEN": access_token,
        }

        ns = {"ebay": "urn:ebay:apis:eBLBaseComponents"}
        page_number = 1
        created, updated = 0, 0

        while True:
            body = f"""<?xml version="1.0" encoding="utf-8"?>
<GetMyeBaySellingRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <RequesterCredentials>
    <eBayAuthToken>{access_token}</eBayAuthToken>
  </RequesterCredentials>
  <ActiveList>
    <Include>true</Include>
    <Pagination>
      <EntriesPerPage>100</EntriesPerPage>
      <PageNumber>{page_number}</PageNumber>
    </Pagination>
  </ActiveList>
</GetMyeBaySellingRequest>
"""

            response = requests.post("https://api.ebay.com/ws/api.dll", headers=headers, data=body)
            if response.status_code != 200:
                self.stderr.write(self.style.ERROR(f"❌ eBay Trading API request failed with status {response.status_code}"))
                self.stderr.write(response.text)
                return

            root = ET.fromstring(response.content)
            active_list = root.find("ebay:ActiveList", ns)
            if active_list is None:
                break

            items = active_list.findall(".//ebay:Item", ns)
            if not items:
                break

            for item in items:
                sku_elem = item.find("ebay:SKU", ns)
                title_elem = item.find("ebay:Title", ns)
                quantity_elem = item.find("ebay:QuantityAvailable", ns)
                price_elem = item.find("ebay:SellingStatus/ebay:CurrentPrice", ns)
                description_elem = item.find("ebay:Description", ns)
                picture_elem = item.find("ebay:PictureDetails/ebay:PictureURL", ns)
                condition_elem = item.find("ebay:ConditionDisplayName", ns)
                location_elem = item.find("ebay:Location", ns)
                item_id_elem = item.find("ebay:ItemID", ns)

                sku = sku_elem.text if sku_elem is not None else None
                title = title_elem.text if title_elem is not None else "No Title"
                quantity = int(quantity_elem.text) if quantity_elem is not None else 0
                price = float(price_elem.text) if price_elem is not None else 0.00
                description = description_elem.text if description_elem is not None else ""
                image_url = picture_elem.text if picture_elem is not None else ""
                condition = condition_elem.text if condition_elem is not None else ""
                location = location_elem.text if location_elem is not None else ""
                listing_url = f"https://www.ebay.com/itm/{item_id_elem.text}" if item_id_elem is not None else ""

                if not sku:
                    continue

                obj, created_flag = Item.objects.update_or_create(
                    sku=sku,
                    defaults={
                        "name": title,
                        "quantity": quantity,
                        "price": price,
                        "description": description,
                        "image_url": image_url,
                        "condition": condition,
                        "location": location,
                        "listing_url": listing_url,
                    }
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

            total_pages_elem = root.find(".//ebay:PaginationResult/ebay:TotalNumberOfPages", ns)
            if total_pages_elem is None or page_number >= int(total_pages_elem.text):
                break

            page_number += 1

        self.stdout.write(f"✅ Synced {created} new and {updated} updated eBay listings into WMS.")

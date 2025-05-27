from django.core.management.base import BaseCommand
from django.conf import settings
from inventory.models import Item
import requests
import xml.etree.ElementTree as ET

class Command(BaseCommand):
    help = "Sync active eBay listings into WMS using Trading API"

    def handle(self, *args, **options):
        print("🚨 models.py is being read!")

        access_token = settings.EBAY_ACCESS_TOKEN

        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-CALL-NAME": "GetMyeBaySelling",
            "X-EBAY-API-SITEID": "0",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-IAF-TOKEN": access_token,
        }

        body = f"""<?xml version="1.0" encoding="utf-8"?>
<GetMyeBaySellingRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <RequesterCredentials>
    <eBayAuthToken>{access_token}</eBayAuthToken>
  </RequesterCredentials>
  <ActiveList>
    <Include>true</Include>
    <Pagination>
      <EntriesPerPage>100</EntriesPerPage>
      <PageNumber>1</PageNumber>
    </Pagination>
  </ActiveList>
</GetMyeBaySellingRequest>
"""

        response = requests.post("https://api.ebay.com/ws/api.dll", headers=headers, data=body)
        if response.status_code != 200:
            self.stderr.write(self.style.ERROR(f"❌ eBay Trading API request failed with status {response.status_code}"))
            self.stderr.write(response.text)
            return

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            self.stderr.write(self.style.ERROR("❌ Failed to parse XML response"))
            self.stderr.write(str(e))
            return

        ns = {"ebay": "urn:ebay:apis:eBLBaseComponents"}
        active_list = root.find("ebay:ActiveList", ns)

        if active_list is None:
            self.stdout.write("✅ No active listings found.")
            return

        items = active_list.findall(".//ebay:Item", ns)
        created, updated = 0, 0

        for item in items:
            sku = item.findtext("ebay:SKU", default=None, namespaces=ns)
            title = item.findtext("ebay:Title", default="No Title", namespaces=ns)
            quantity_text = item.findtext("ebay:Quantity", default="0", namespaces=ns)
            price_text = item.findtext("ebay:StartPrice", default="0.00", namespaces=ns)

            try:
                quantity = int(quantity_text)
            except ValueError:
                quantity = 0

            try:
                price = float(price_text)
            except ValueError:
                price = 0.00

            if not sku:
                continue

            obj, created_flag = Item.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": title,
                    "quantity": quantity,
                    "price": price,
                }
            )
            if created_flag:
                created += 1
            else:
                updated += 1

        self.stdout.write(f"✅ Synced {created} new and {updated} updated eBay listings into WMS.")

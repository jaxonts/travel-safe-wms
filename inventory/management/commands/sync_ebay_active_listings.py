from django.core.management.base import BaseCommand
from django.conf import settings
from inventory.models import Item
import requests

class Command(BaseCommand):
    help = "Sync active eBay listings using Trading API into WMS"

    def handle(self, *args, **options):
        print("🚨 models.py is being read!")

        access_token = settings.EBAY_ACCESS_TOKEN
        app_id = settings.EBAY_CLIENT_ID

        url = "https://api.ebay.com/ws/api.dll"
        headers = {
            "X-EBAY-API-CALL-NAME": "GetMyeBaySelling",
            "X-EBAY-API-SITEID": "0",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-APP-NAME": app_id,
            "Content-Type": "text/xml",
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

        try:
            response = requests.post(url, headers=headers, data=body)
            if response.status_code != 200:
                self.stderr.write(self.style.ERROR(f"❌ API error: {response.status_code}"))
                self.stderr.write(response.text)
                return

            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.text)

            namespace = {'ns': 'urn:ebay:apis:eBLBaseComponents'}
            listings = root.findall(".//ns:Item", namespace)

            if not listings:
                self.stdout.write("✅ No active listings found.")
                return

            created = 0
            for item in listings:
                sku = item.findtext("ns:SKU", default=None, namespaces=namespace)
                title = item.findtext("ns:Title", default="Untitled", namespaces=namespace)

                if not sku:
                    continue

                _, created_flag = Item.objects.update_or_create(
                    sku=sku,
                    defaults={"name": title}
                )
                if created_flag:
                    created += 1

            self.stdout.write(f"✅ Synced {created} active eBay listings into WMS.")

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Sync error: {str(e)}"))


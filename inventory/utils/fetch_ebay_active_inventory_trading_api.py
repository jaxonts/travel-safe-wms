import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def get_ebay_active_inventory():
    EBAY_USER_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
    EBAY_DEV_ID = os.getenv("EBAY_DEV_ID")
    EBAY_APP_ID = os.getenv("EBAY_APP_ID")
    EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")

    if not all([EBAY_USER_TOKEN, EBAY_DEV_ID, EBAY_APP_ID, EBAY_CERT_ID]):
        print("❌ Missing eBay API credentials.")
        return []

    headers = {
        "Content-Type": "text/xml",
        "X-EBAY-API-CALL-NAME": "GetSellerList",
        "X-EBAY-API-SITEID": "0",
        "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
        "X-EBAY-API-DEV-NAME": EBAY_DEV_ID,
        "X-EBAY-API-APP-NAME": EBAY_APP_ID,
        "X-EBAY-API-CERT-NAME": EBAY_CERT_ID,
    }

    now = datetime.utcnow()
    start_time = (now - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_time = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    all_items = []
    page_number = 1
    has_more_items = True

    while has_more_items:
        body = f"""<?xml version="1.0" encoding="utf-8"?>
        <GetSellerListRequest xmlns="urn:ebay:apis:eBLBaseComponents">
          <RequesterCredentials>
            <eBayAuthToken>{EBAY_USER_TOKEN}</eBayAuthToken>
          </RequesterCredentials>
          <Pagination>
            <EntriesPerPage>100</EntriesPerPage>
            <PageNumber>{page_number}</PageNumber>
          </Pagination>
          <StartTimeFrom>{start_time}</StartTimeFrom>
          <StartTimeTo>{end_time}</StartTimeTo>
          <IncludeVariations>true</IncludeVariations>
          <GranularityLevel>Fine</GranularityLevel>
          <DetailLevel>ReturnAll</DetailLevel>
        </GetSellerListRequest>"""

        try:
            response = requests.post("https://api.ebay.com/ws/api.dll", data=body, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Error fetching page {page_number}: {e}")
            break

        root = ET.fromstring(response.text)
        namespace = {"ns": "urn:ebay:apis:eBLBaseComponents"}

        items = root.findall(".//ns:Item", namespace)
        if not items:
            print(f"⚠️ No items found on page {page_number}.")
            break

        for item in items:
            sku_elem = item.find("ns:SKU", namespace)
            title = item.findtext("ns:Title", default="No Title", namespaces=namespace)
            price = item.findtext("ns:StartPrice", default="0", namespaces=namespace)
            quantity = item.findtext("ns:Quantity", default="0", namespaces=namespace)
            description = item.findtext("ns:Description", default="", namespaces=namespace)
            item_id = item.findtext("ns:ItemID", namespaces=namespace)
            location = item.findtext("ns:Location", default="", namespaces=namespace)
            condition = item.findtext("ns:ConditionDisplayName", default="", namespaces=namespace)

            picture_url = ""
            pic_elem = item.find(".//ns:PictureURL", namespace)
            if pic_elem is not None:
                picture_url = pic_elem.text

            custom_sku = sku_elem.text if sku_elem is not None else item_id

            all_items.append({
                "sku": custom_sku.strip(),
                "name": title.strip(),
                "description": description.strip(),
                "price": float(price),
                "quantity": int(quantity),
                "location": location,
                "condition": condition,
                "image_url": picture_url,
                "listing_url": f"https://www.ebay.com/itm/{item_id}",
                "source": "eBay",
            })

        has_more_items_elem = root.find(".//ns:HasMoreItems", namespace)
        has_more_items = has_more_items_elem is not None and has_more_items_elem.text == "true"
        page_number += 1

    return all_items

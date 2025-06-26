import os
import requests

def get_ebay_active_inventory():
    access_token = os.getenv("EBAY_ACCESS_TOKEN")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    endpoint = "https://api.ebay.com/sell/inventory/v1/offer"
    items = []
    limit = 100
    offset = 0

    while True:
        url = f"{endpoint}?limit={limit}&offset={offset}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch inventory: {response.status_code}")
            print(response.json())
            break

        data = response.json()
        offers = data.get("offers", [])

        for offer in offers:
            sku = offer.get("sku")
            title = offer.get("listing", {}).get("title", "No Title")
            items.append({"sku": sku, "title": title})

        if len(offers) < limit:
            break

        offset += limit

    print(f"✅ Pulled {len(items)} active offers from eBay.")
    return items




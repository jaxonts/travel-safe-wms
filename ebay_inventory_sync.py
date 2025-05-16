import requests

EBAY_OAUTH_TOKEN = "v^1.1#i^1#f^0#r^0#p^3#I^3#t^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"

headers = {
    "Authorization": f"Bearer {EBAY_OAUTH_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def fetch_inventory_items():
    url = "https://api.ebay.com/sell/inventory/v1/inventory_item"
    limit = 50
    offset = 0

    while True:
        params = {
            "limit": limit,
            "offset": offset
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            items = data.get("inventoryItems", [])
            if not items:
                print("✅ No more items to fetch.")
                break

            for item in items:
                sku = item.get("sku")
                title = item.get("product", {}).get("title")
                quantity = item.get("availability", {}).get("shipToLocationAvailability", {}).get("quantity")
                print(f"SKU: {sku} | Title: {title} | Quantity: {quantity}")

            offset += limit
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            break

if __name__ == "__main__":
    fetch_inventory_items()

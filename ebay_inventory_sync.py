import requests

EBAY_OAUTH_TOKEN = "v^1.1#i^1#r^3#r^1#f^0#p^3#t^Ul4xMF83OkMwQzc0RTE1MTMyMTYyODYzNTE2MTc5NzM3RDExMkMwXzFfMSNFXjI2MA=="

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

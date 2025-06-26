import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_ebay_active_inventory():
    access_token = os.getenv("EBAY_ACCESS_TOKEN")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    url = "https://api.ebay.com/sell/inventory/v1/inventory_item"
    params = {
        "limit": 1000
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("inventoryItems", [])
        else:
            print("❌ Failed to fetch inventory:", response.status_code)
            print(response.json())
            return []
    except Exception as e:
        print("❌ Error fetching inventory:", e)
        return []

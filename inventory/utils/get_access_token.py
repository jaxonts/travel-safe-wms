import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_access_token_from_refresh_token():
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {os.getenv('EBAY_BASE64_ENCODED_CREDENTIALS')}"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": os.getenv("EBAY_REFRESH_TOKEN"),
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory"
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    access_token = response.json()["access_token"]
    return access_token

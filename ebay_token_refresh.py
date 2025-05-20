import requests
import base64
import urllib.parse

# ✅ Replace with your actual values
EBAY_CLIENT_ID = "TravelSa-TravelSa-PRD-3a70f81c3-b1e944ab"
EBAY_CLIENT_SECRET = "PRD-a70f81c31035-0d5f-4b5a-aa47-3b01"
EBAY_REFRESH_TOKEN = "v^1.1#i^1#r^1#I^3#f^0#p^3#t^Ul4xMF8xOjZDQzIzMUFDNTlCNTA4MTU5OUM0MzY4NzJFQUU5MzFGXzFfMSNFXjI2MA=="

url = "https://api.ebay.com/identity/v1/oauth2/token"

credentials = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {encoded_credentials}",
}

data = {
    "grant_type": "refresh_token",
    "refresh_token": EBAY_REFRESH_TOKEN,
    "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory"
}

response = requests.post(url, headers=headers, data=urllib.parse.urlencode(data))
print(response.json())

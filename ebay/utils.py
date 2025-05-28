import requests
from django.conf import settings

def refresh_ebay_access_token():
    """
    Refreshes the eBay user access token using the long-lived refresh token.
    The new access token is stored in Django settings for immediate use.
    """
    url = "https://api.ebay.com/identity/v1/oauth2/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {settings.EBAY_BASE64_ENCODED_CREDENTIALS}"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": settings.EBAY_REFRESH_TOKEN,
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        raise Exception(f"❌ Failed to refresh token: {response.status_code} - {response.text}")

    response_data = response.json()
    new_token = response_data.get("access_token")

    if not new_token:
        raise Exception("❌ No access_token returned in the response.")

    # Temporarily update token for this session
    settings.EBAY_ACCESS_TOKEN = new_token
    print("🔄 Refreshed eBay access token.")

    return new_token

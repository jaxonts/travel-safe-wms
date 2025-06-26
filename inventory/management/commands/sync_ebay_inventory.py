from .fetch_ebay_active_inventory_trading_api import get_ebay_active_inventory
from inventory.models import Item

def sync_ebay_inventory(verbose=False):
    print("🔄 Syncing eBay inventory with WMS...")

    items = get_ebay_active_inventory()

    if not isinstance(items, list):
        raise Exception("❌ Expected a list of dicts from eBay, got something else.")

    if verbose:
        print(f"🧪 Raw item dump (truncated): {items[:1]}")

    count = 0

    for listing in items:
        if not isinstance(listing, dict):
            print("⚠️ Skipping item (not a dict):", listing)
            continue

        sku = listing.get("sku")
        name = listing.get("name", "")
        quantity = listing.get("quantity", 0)
        price = listing.get("price", 0.00)
        description = listing.get("description", "")
        image_url = listing.get("image_url", "")
        condition = listing.get("condition", "")
        location = listing.get("location", "")
        listing_url = listing.get("listing_url", "")
        source = listing.get("source", "eBay")

        if not sku:
            print("⚠️ Skipping item with missing SKU")
            continue

        obj, created = Item.objects.update_or_create(
            sku=sku,
            defaults={
                "name": name,
                "quantity": quantity,
                "price": price,
                "description": description,
                "image_url": image_url,
                "condition": condition,
                "location": location,
                "listing_url": listing_url,
                "source": source,
            }
        )

        count += 1
        if verbose:
            print(f"{'🆕 Created' if created else '🔁 Updated'} item: {sku} - {name}")

    print(f"✅ Fetched {len(items)} active listings from eBay")
    print(f"🟢 Imported/updated {count} items.")

from inventory.models import Item
from .fetch_ebay_active_inventory_trading_api import get_ebay_active_inventory

def sync_ebay_inventory(verbose=False):
    if verbose:
        print("🚨 models.py is being read!")

    print("\n🔄 Syncing eBay inventory with WMS...")

    items = get_ebay_active_inventory()
    if verbose and items:
        print("🧪 Raw item dump (truncated):", items[:1])

    imported = 0
    updated = 0

    for data in items:
        sku = data.get("sku")
        if not sku:
            continue

        obj, created = Item.objects.get_or_create(sku=sku)

        # Only update selected fields (leave WMS-specific fields like bin_location untouched)
        obj.name = data.get("name", obj.name)
        obj.price = data.get("price", obj.price)
        obj.quantity = data.get("quantity", obj.quantity)
        obj.description = data.get("description", obj.description)
        obj.image_url = data.get("image_url", obj.image_url)
        obj.listing_url = data.get("listing_url", obj.listing_url)
        obj.condition = data.get("condition", obj.condition)
        obj.location = data.get("location", obj.location)
        obj.source = data.get("source", obj.source)

        obj.save()

        if created:
            imported += 1
            print(f"🆕 Created item: {sku} - {obj.name}")
        else:
            updated += 1
            print(f"🔁 Updated item: {sku} - {obj.name}")

    print(f"✅ Fetched {len(items)} active listings from eBay")
    print(f"🟢 Imported/updated {imported + updated} items.")


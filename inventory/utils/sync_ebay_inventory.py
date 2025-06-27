from inventory.models import Item
from .fetch_ebay_active_inventory_trading_api import get_ebay_active_inventory

def sync_ebay_inventory(verbose=False):
    if verbose:
        print("🚨 models.py is being read!")

    print("\n🔄 Syncing eBay inventory with WMS...")

    items = get_ebay_active_inventory()

    # Ensure we have a list
    if not isinstance(items, list):
        print("❌ Invalid response format. Expected a list.")
        return

    if verbose:
        print(f"🧪 Raw item dump (showing 1 of {len(items)}): {items[:1]}")

    if not items:
        print("⚠️ No items returned by eBay API. Check credentials or response.")
        return

    imported = 0
    updated = 0

    for data in items:
        sku = data.get("sku")
        if not sku:
            print("⚠️ Skipping item with missing SKU:", data)
            continue

        obj, created = Item.objects.get_or_create(sku=sku)

        # Only update fields that are meant to be overwritten
        obj.name = data.get("name", obj.name)
        obj.price = data.get("price", obj.price or 0)
        obj.quantity = data.get("quantity", obj.quantity or 0)
        obj.description = data.get("description", obj.description or "")
        obj.image_url = data.get("image_url", obj.image_url or "")
        obj.listing_url = data.get("listing_url", obj.listing_url or "")
        obj.condition = data.get("condition", obj.condition or "")
        obj.location = data.get("location", obj.location or "")
        obj.source = data.get("source", obj.source or "eBay")

        obj.save()

        if created:
            imported += 1
            print(f"🆕 Created item: {sku} - {obj.name}")
        else:
            updated += 1
            print(f"🔁 Updated item: {sku} - {obj.name}")

    print(f"✅ Fetched {len(items)} active listings from eBay")
    print(f"🟢 Imported: {imported}, Updated: {updated}")

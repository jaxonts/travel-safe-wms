from inventory.models import Item
from .fetch_ebay_active_inventory_trading_api import get_ebay_active_inventory


def _extract_sku_suffix(sku):
    sku = (sku or "").strip()

    if "#" not in sku:
        return ""

    return sku.rsplit("#", 1)[1].strip()


def _extract_ebay_item_number(data):
    """
    Try common keys returned by eBay helpers/APIs.
    """
    for key in (
        "ebay_item_number",
        "item_number",
        "item_id",
        "listing_id",
    ):
        value = data.get(key)

        if value is not None and str(value).strip():
            value = str(value).strip()

            if value.endswith(".0") and value[:-2].isdigit():
                value = value[:-2]

            return value

    return ""


def _find_existing_item(sku, sku_suffix, ebay_item_number):
    """
    Match priority:

    1. eBay Item Number
    2. SKU suffix after final #
    3. Exact SKU

    Never guess when multiple records match.
    """

    if ebay_item_number:
        obj = Item.objects.filter(
            ebay_item_number=ebay_item_number
        ).first()

        if obj:
            return obj

    if sku_suffix:
        matches = Item.objects.filter(
            sku__endswith=f"#{sku_suffix}"
        ).order_by("id")

        count = matches.count()

        if count == 1:
            return matches.first()

        if count > 1:
            exact_matches = matches.filter(sku=sku)

            if exact_matches.count() == 1:
                return exact_matches.first()

            raise ValueError(
                f"Ambiguous SKU suffix #{sku_suffix}: "
                f"{count} WMS items already use this suffix. "
                "An eBay Item Number is required."
            )

    exact_matches = Item.objects.filter(sku=sku).order_by("id")

    if exact_matches.count() == 1:
        return exact_matches.first()

    if exact_matches.count() > 1:
        raise ValueError(
            f"Ambiguous SKU {sku}: multiple WMS items already use this SKU. "
            "An eBay Item Number is required."
        )

    return None


def sync_ebay_inventory(verbose=False):
    if verbose:
        print("models.py is being read")

    print("\nSyncing eBay inventory with WMS...")

    items = get_ebay_active_inventory()

    if not isinstance(items, list):
        print("Invalid response format. Expected a list.")
        return

    if verbose:
        print(
            f"Raw item dump (showing 1 of {len(items)}): "
            f"{items[:1]}"
        )

    if not items:
        print(
            "No items returned by eBay API. "
            "Check credentials or response."
        )
        return

    imported = 0
    updated = 0
    errors = 0

    for data in items:
        sku = (data.get("sku") or "").strip()

        if not sku:
            print("Skipping item with missing SKU:", data)
            continue

        sku_suffix = _extract_sku_suffix(sku)
        ebay_item_number = _extract_ebay_item_number(data)

        try:
            obj = _find_existing_item(
                sku=sku,
                sku_suffix=sku_suffix,
                ebay_item_number=ebay_item_number,
            )

            created = obj is None

            if created:
                obj = Item(
                    sku=sku,
                    name=data.get("name") or sku,
                )
            else:
                # Prefix/location changes on eBay should update
                # the existing WMS listing, not create another.
                obj.sku = sku

            if ebay_item_number:
                obj.ebay_item_number = ebay_item_number

            obj.name = data.get("name") or obj.name or sku
            obj.price = data.get("price") or obj.price or 0
            obj.description = (
                data.get("description")
                or obj.description
                or ""
            )
            obj.image_url = (
                data.get("image_url")
                or obj.image_url
                or ""
            )
            obj.listing_url = (
                data.get("listing_url")
                or obj.listing_url
                or ""
            )
            obj.condition = (
                data.get("condition")
                or obj.condition
                or ""
            )
            obj.location = (
                data.get("location")
                or obj.location
                or ""
            )
            obj.source = (
                data.get("source")
                or obj.source
                or "eBay"
            )

            obj.save()

            if created:
                imported += 1
                print(f"Created item: {sku} - {obj.name}")
            else:
                updated += 1
                print(f"Updated item: {sku} - {obj.name}")

        except Exception as exc:
            errors += 1
            print(f"ERROR syncing {sku}: {exc}")

    print(f"Fetched {len(items)} active listings from eBay")
    print(
        f"Imported: {imported}, "
        f"Updated: {updated}, "
        f"Errors: {errors}"
    )

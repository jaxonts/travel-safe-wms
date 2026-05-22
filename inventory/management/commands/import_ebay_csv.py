import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import Item, Source, Bin, InventoryBalance, InventoryMovement


def _to_int(value, default=0):
    try:
        if value is None:
            return default
        s = str(value).strip()
        if s == "":
            return default
        return int(float(s))
    except Exception:
        return default


def _to_decimal(value, default=Decimal("0.00")):
    try:
        if value is None:
            return default
        s = str(value).strip().replace("$", "").replace(",", "")
        if s == "":
            return default
        return Decimal(s)
    except (InvalidOperation, Exception):
        return default


class Command(BaseCommand):
    help = "Import eBay 'All active listings' CSV into WMS Items (optionally set quantities into a bin)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the eBay active listings CSV file")
        parser.add_argument("--source-name", type=str, default="Main Facility", help="Source (facility) name")
        parser.add_argument("--bin-code", type=str, default="DEFAULT", help="Bin code to place imported quantities into")
        parser.add_argument(
            "--set-qty",
            action="store_true",
            help="Set quantities into InventoryBalance via InventoryMovement ADJUST diffs (idempotent).",
        )
        parser.add_argument(
            "--commit-every",
            type=int,
            default=200,
            help="Commit every N rows (faster on SQLite, shows progress).",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"]).expanduser()
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f"CSV not found: {csv_path}"))
            return

        # Ensure target Source + Bin exist
        src, _ = Source.objects.get_or_create(
            name=options["source_name"], defaults={"is_main_facility": True}
        )
        bin_obj, _ = Bin.objects.get_or_create(code=options["bin_code"], defaults={"location": src})

        created_items = 0
        updated_items = 0
        qty_changes = 0
        skipped = 0
        processed = 0
        commit_every = max(1, int(options["commit_every"]))

        with csv_path.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            required_cols = {"Custom label (SKU)", "Title", "Item number"}
            missing = required_cols - set(reader.fieldnames or [])
            if missing:
                self.stderr.write(self.style.ERROR(f"CSV missing columns: {sorted(missing)}"))
                self.stderr.write(self.style.ERROR(f"Found columns: {reader.fieldnames}"))
                return

            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= commit_every:
                    c, u, q, s, p = self._process_batch(batch, bin_obj, options["set_qty"])
                    created_items += c
                    updated_items += u
                    qty_changes += q
                    skipped += s
                    processed += p
                    batch = []
                    self.stdout.write(f"Processed {processed} rows...")

            # last partial batch
            if batch:
                c, u, q, s, p = self._process_batch(batch, bin_obj, options["set_qty"])
                created_items += c
                updated_items += u
                qty_changes += q
                skipped += s
                processed += p

        self.stdout.write(self.style.SUCCESS("✅ eBay CSV import complete"))
        self.stdout.write(f"Rows processed: {processed}")
        self.stdout.write(f"Items created: {created_items}")
        self.stdout.write(f"Items updated: {updated_items}")
        self.stdout.write(f"Qty changes applied: {qty_changes}" if options["set_qty"] else "Qty changes applied: (skipped)")
        self.stdout.write(f"Rows skipped (missing SKU): {skipped}")
        self.stdout.write(f"Imported into bin: {src.name} / {bin_obj.code}")

    @transaction.atomic
    def _process_batch(self, rows, bin_obj, set_qty: bool):
        created_items = 0
        updated_items = 0
        qty_changes = 0
        skipped = 0
        processed = 0

        for row in rows:
            sku = (row.get("Custom label (SKU)") or "").strip()
            title = (row.get("Title") or "").strip()
            item_number = (row.get("Item number") or "").strip()

            if not sku:
                skipped += 1
                continue

            listing_url = f"https://www.ebay.com/itm/{item_number}" if item_number else ""

            price = _to_decimal(row.get("Start price"))
            if price == Decimal("0.00"):
                price = _to_decimal(row.get("Current price"))

            condition = (row.get("Condition") or "").strip()

            defaults = {
                "name": title or sku,
                "price": price,
                "condition": condition,
                "listing_url": listing_url,
                "source": "eBay",
            }

            # Avoid update_or_create savepoint overhead: try get, then create/update
            obj = Item.objects.filter(sku=sku).first()
            if obj is None:
                obj = Item(sku=sku, **defaults)
                obj.save()
                created_items += 1
            else:
                # update only if changed (reduces writes)
                changed = False
                for k, v in defaults.items():
                    if getattr(obj, k) != v:
                        setattr(obj, k, v)
                        changed = True
                if changed:
                    obj.save(update_fields=list(defaults.keys()))
                updated_items += 1

            if set_qty:
                desired_qty = _to_int(row.get("Available quantity"), default=0)
                bal, _ = InventoryBalance.objects.get_or_create(item=obj, bin=bin_obj, defaults={"quantity": 0})
                current_qty = int(bal.quantity)

                diff = desired_qty - current_qty
                if diff != 0:
                    if diff > 0:
                        InventoryMovement.objects.create(
                            item=obj,
                            movement_type="ADJUST",
                            quantity=diff,
                            to_bin=bin_obj,
                            performed_by=None,
                            note=f"CSV import set qty to {desired_qty} (was {current_qty})",
                        )
                    else:
                        InventoryMovement.objects.create(
                            item=obj,
                            movement_type="ADJUST",
                            quantity=abs(diff),
                            from_bin=bin_obj,
                            performed_by=None,
                            note=f"CSV import set qty to {desired_qty} (was {current_qty})",
                        )
                    qty_changes += 1

            processed += 1

        return created_items, updated_items, qty_changes, skipped, processed

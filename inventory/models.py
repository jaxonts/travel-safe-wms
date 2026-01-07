from django.db import models, transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class Source(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    is_main_facility = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Bin(models.Model):
    code = models.CharField(max_length=100, unique=True)
    location = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="bins")

    def __str__(self):
        return f"{self.location.name} - Bin {self.code}"

    class Meta:
        ordering = ["location__name", "code"]
        indexes = [
            models.Index(fields=["location", "code"]),
        ]


class Item(models.Model):
    """
    Represents a SKU / catalog item. Quantity is NOT stored here.
    Quantities are stored per-bin in InventoryBalance.
    """

    SOURCE_CHOICES = (
        ("eBay", "eBay"),
        ("Manual", "Manual"),
        ("Other", "Other"),
    )

    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    condition = models.CharField(max_length=100, blank=True)

    # Keep your legacy "location" string if you still use it in UI,
    # but the real physical location is Bin + Source.
    location = models.CharField(max_length=255, blank=True)

    listing_url = models.URLField(blank=True, default="")

    # Keeping as a string to avoid breaking existing integrations quickly.
    # If you want, we can convert this to a FK later.
    source = models.CharField(max_length=100, default="eBay", choices=SOURCE_CHOICES)

    def __str__(self):
        return f"{self.sku} - {self.name}"

    @property
    def total_quantity(self) -> int:
        # Convenience for templates/admin; avoid using in huge list pages.
        return int(self.balances.aggregate(total=models.Sum("quantity"))["total"] or 0)

    class Meta:
        ordering = ["sku"]
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["source"]),
        ]


class InventoryBalance(models.Model):
    """
    Quantity for a given Item in a given Bin.
    This is the authoritative stock level by bin.
    """

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="balances")
    bin = models.ForeignKey(Bin, on_delete=models.CASCADE, related_name="balances")
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.item.sku} @ {self.bin.code}: {self.quantity}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["item", "bin"], name="uniq_item_bin_balance"),
            models.CheckConstraint(check=models.Q(quantity__gte=0), name="balance_qty_nonnegative"),
        ]
        indexes = [
            models.Index(fields=["item", "bin"]),
            models.Index(fields=["bin"]),
        ]


class InventoryMovement(models.Model):
    MOVEMENT_TYPES = (
        ("RECEIVE", "Received"),
        ("TRANSFER", "Transferred"),
        ("PICK", "Picked for Order"),
        ("RETURN", "Returned"),
        ("ADJUST", "Adjusted"),
    )

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="movements")

    from_bin = models.ForeignKey(
        Bin, on_delete=models.SET_NULL, null=True, blank=True, related_name="movements_out"
    )
    to_bin = models.ForeignKey(
        Bin, on_delete=models.SET_NULL, null=True, blank=True, related_name="movements_in"
    )

    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Optional notes field (useful for audits)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.movement_type} - {self.quantity} of {self.item.sku}"

    def clean(self):
        super().clean()

        if self.quantity is None or self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be > 0."})

        mt = self.movement_type

        if mt == "RECEIVE":
            if not self.to_bin:
                raise ValidationError({"to_bin": "RECEIVE requires to_bin."})
        elif mt == "RETURN":
            if not self.to_bin:
                raise ValidationError({"to_bin": "RETURN requires to_bin."})
        elif mt == "PICK":
            if not self.from_bin:
                raise ValidationError({"from_bin": "PICK requires from_bin."})
        elif mt == "TRANSFER":
            if not self.from_bin or not self.to_bin:
                raise ValidationError("TRANSFER requires both from_bin and to_bin.")
            if self.from_bin_id == self.to_bin_id:
                raise ValidationError("TRANSFER requires from_bin and to_bin to be different.")
        elif mt == "ADJUST":
            # For ADJUST you can choose either from_bin (negative adjustment) or to_bin (positive adjustment)
            # but not both at once to keep it unambiguous.
            if self.from_bin and self.to_bin:
                raise ValidationError("ADJUST should use either from_bin (decrease) OR to_bin (increase), not both.")
            if not self.from_bin and not self.to_bin:
                raise ValidationError("ADJUST requires from_bin (decrease) or to_bin (increase).")

    @staticmethod
    def _get_or_create_balance(item: Item, bin_obj: Bin) -> InventoryBalance:
        # Lock row to prevent race conditions under concurrency
        balance, _ = InventoryBalance.objects.select_for_update().get_or_create(
            item=item, bin=bin_obj, defaults={"quantity": 0}
        )
        return balance

    @staticmethod
    def _increase(item: Item, bin_obj: Bin, qty: int):
        InventoryBalance.objects.update_or_create(
            item=item,
            bin=bin_obj,
            defaults={},
        )
        # Use F() for concurrency-safe increment
        InventoryBalance.objects.filter(item=item, bin=bin_obj).update(quantity=F("quantity") + qty)

    @staticmethod
    def _decrease(item: Item, bin_obj: Bin, qty: int):
        # Lock the balance row, then validate and decrement safely
        bal = InventoryMovement._get_or_create_balance(item, bin_obj)
        bal.refresh_from_db()

        if bal.quantity < qty:
            raise ValidationError(
                f"Insufficient stock for {item.sku} in bin {bin_obj.code}: have {bal.quantity}, need {qty}."
            )

        InventoryBalance.objects.filter(pk=bal.pk).update(quantity=F("quantity") - qty)

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # Validate first
        self.full_clean()

        # Only apply stock effects on initial creation (prevents double-applying on edits)
        if not is_new:
            return super().save(*args, **kwargs)

        with transaction.atomic():
            # Apply inventory effects
            mt = self.movement_type
            qty = int(self.quantity)

            if mt in ("RECEIVE", "RETURN"):
                self._increase(self.item, self.to_bin, qty)

            elif mt == "PICK":
                self._decrease(self.item, self.from_bin, qty)

            elif mt == "TRANSFER":
                self._decrease(self.item, self.from_bin, qty)
                self._increase(self.item, self.to_bin, qty)

            elif mt == "ADJUST":
                # from_bin => decrease, to_bin => increase
                if self.from_bin:
                    self._decrease(self.item, self.from_bin, qty)
                else:
                    self._increase(self.item, self.to_bin, qty)

            return super().save(*args, **kwargs)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["item", "-timestamp"]),
            models.Index(fields=["movement_type", "-timestamp"]),
        ]

print("🚨 models.py is being read!")

from django.db import models
from django.contrib.auth.models import User

class Source(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    is_main_facility = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Bin(models.Model):
    code = models.CharField(max_length=100, unique=True)
    location = models.ForeignKey(Source, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.location.name} - Bin {self.code}"

    class Meta:
        ordering = ['location__name', 'code']

class Item(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    quantity = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    condition = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)
    listing_url = models.URLField(blank=True, default="")
    bin = models.ForeignKey(Bin, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.CharField(max_length=100, default='eBay')

    def __str__(self):
        return f"{self.sku} - {self.name}"

    class Meta:
        ordering = ['sku']

class InventoryMovement(models.Model):
    MOVEMENT_TYPES = (
        ('RECEIVE', 'Received'),
        ('TRANSFER', 'Transferred'),
        ('PICK', 'Picked for Order'),
        ('RETURN', 'Returned'),
    )

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    from_bin = models.ForeignKey(Bin, on_delete=models.SET_NULL, null=True, related_name='movements_out')
    to_bin = models.ForeignKey(Bin, on_delete=models.SET_NULL, null=True, related_name='movements_in')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.movement_type} - {self.quantity} of {self.item.sku}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.movement_type in ['RECEIVE', 'TRANSFER', 'RETURN'] and self.to_bin:
            self.item.bin = self.to_bin
            self.item.save()

    class Meta:
        ordering = ['-timestamp']

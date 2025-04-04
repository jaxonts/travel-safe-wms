print("🚨 models.py is being read!")
from django.db import models
from django.contrib.auth.models import User

class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    is_main_facility = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Bin(models.Model):
    code = models.CharField(max_length=100, unique=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.location.name} - Bin {self.code}"

class Item(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    quantity = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    bin = models.ForeignKey(Bin, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.sku} - {self.name}"

class InventoryMovement(models.Model):
    MOVEMENT_TYPES = (
        ('RECEIVE', 'Received'),
        ('TRANSFER', 'Transferred'),
        ('PICK', 'Picked for Order'),
        ('RETURN', 'Returned'),
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    from_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='from_location')
    to_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='to_location')
    quantity = models.IntegerField()
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.item.sku} - {self.movement_type} {self.quantity}"




# Generated by Django 5.2 on 2025-05-07 18:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_remove_inventorymovement_from_location_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Location',
            new_name='Source',
        ),
    ]

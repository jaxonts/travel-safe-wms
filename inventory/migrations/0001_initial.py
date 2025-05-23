# Generated by Django 5.2 on 2025-04-03 22:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('address', models.TextField(blank=True)),
                ('is_main_facility', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('sku', models.CharField(max_length=100, unique=True)),
                ('quantity', models.IntegerField(default=0)),
                ('description', models.TextField(blank=True)),
                ('bin', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.bin')),
            ],
        ),
        migrations.CreateModel(
            name='InventoryMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('movement_type', models.CharField(choices=[('RECEIVE', 'Received'), ('TRANSFER', 'Transferred'), ('PICK', 'Picked for Order'), ('RETURN', 'Returned')], max_length=20)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('performed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.item')),
                ('from_location', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='from_location', to='inventory.location')),
                ('to_location', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='to_location', to='inventory.location')),
            ],
        ),
        migrations.AddField(
            model_name='bin',
            name='location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.location'),
        ),
    ]

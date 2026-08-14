from django.db import migrations, models


def backfill_sku_suffix(apps, schema_editor):
    """
    Populate sku_suffix for all existing inventory records.

    Example:
        TSWP91#1711 -> 1711

    If an SKU has no #, sku_suffix remains blank.
    """
    Item = apps.get_model("inventory", "Item")

    for item in Item.objects.all().iterator():
        sku = (item.sku or "").strip()

        if "#" in sku:
            suffix = sku.rsplit("#", 1)[1].strip()
        else:
            suffix = ""

        Item.objects.filter(pk=item.pk).update(
            sku_suffix=suffix
        )


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0006_alter_item_sku"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="ebay_item_number",
            field=models.CharField(
                blank=True,
                max_length=50,
                null=True,
                unique=True,
            ),
        ),

        migrations.AddField(
            model_name="item",
            name="sku_suffix",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                editable=False,
                max_length=100,
            ),
        ),

        migrations.AlterField(
            model_name="item",
            name="sku",
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
            ),
        ),

        migrations.RunPython(
            backfill_sku_suffix,
            migrations.RunPython.noop,
        ),
    ]

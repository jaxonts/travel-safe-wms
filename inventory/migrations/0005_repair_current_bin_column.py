from django.db import migrations, connection


def repair_current_bin_column(apps, schema_editor):
    table = "inventory_item"
    column = "current_bin_id"

    with connection.cursor() as cursor:
        vendor = connection.vendor

        if vendor == "postgresql":
            cursor.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "{column}" bigint NULL;')
            cursor.execute(
                f'CREATE INDEX IF NOT EXISTS "{table}_{column}_idx" ON "{table}" ("{column}");'
            )

            cursor.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'inventory_item_current_bin_id_fk'
                    ) THEN
                        ALTER TABLE inventory_item
                        ADD CONSTRAINT inventory_item_current_bin_id_fk
                        FOREIGN KEY (current_bin_id)
                        REFERENCES inventory_bin (id)
                        DEFERRABLE INITIALLY DEFERRED;
                    END IF;
                END $$;
                """
            )

        elif vendor == "sqlite":
            cursor.execute(f'ALTER TABLE "{table}" ADD COLUMN "{column}" integer NULL;')

        else:
            cursor.execute(f'ALTER TABLE "{table}" ADD COLUMN "{column}" integer NULL;')


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0004_item_current_bin"),
    ]

    operations = [
        migrations.RunPython(repair_current_bin_column, migrations.RunPython.noop),
    ]

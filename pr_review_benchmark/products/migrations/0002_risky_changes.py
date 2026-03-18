from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="warehouse_location",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="email",
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.RenameField(
            model_name="product",
            old_name="sku",
            new_name="product_code",
        ),
        migrations.AlterField(
            model_name="product",
            name="description",
            field=models.TextField(blank=True, db_index=True),
        ),
        migrations.RemoveField(
            model_name="product",
            name="is_active",
        ),
        migrations.RemoveField(
            model_name="supplier",
            name="is_active",
        ),
    ]

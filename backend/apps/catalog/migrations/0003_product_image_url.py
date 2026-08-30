from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_remove_product_pote_requires_size_and_bounds_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="image_url",
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]

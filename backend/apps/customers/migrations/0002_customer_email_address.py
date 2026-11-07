from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0001_pr1_customer_order_customer_fk"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name="customer",
            name="default_address",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddConstraint(
            model_name="customer",
            constraint=models.UniqueConstraint(fields=("merchant", "email"), name="uniq_customer_email_per_merchant"),
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["merchant", "email"], name="customers_cu_merchan_3c2f8e_idx"),
        ),
    ]

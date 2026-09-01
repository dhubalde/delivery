from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenancy", "0003_add_employee_roles_and_collected_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="merchant",
            name="logo",
            field=models.ImageField(blank=True, null=True, upload_to="merchant_logos/"),
        ),
        migrations.AddField(
            model_name="merchant",
            name="logo_url",
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]

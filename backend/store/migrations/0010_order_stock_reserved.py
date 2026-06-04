from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0009_order_discount_amounts'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='stock_reserved',
            field=models.BooleanField(default=True),
        ),
    ]

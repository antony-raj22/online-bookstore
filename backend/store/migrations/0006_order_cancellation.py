from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_order_razorpay_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='cancellation_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='order',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

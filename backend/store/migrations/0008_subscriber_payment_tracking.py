from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_subscriber_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriber',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('awaiting_payment', 'Awaiting Payment'),
                    ('paid', 'Paid'),
                    ('failed', 'Failed'),
                ],
                default='awaiting_payment',
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name='subscriber',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='subscriber',
            name='razorpay_payment_id',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='subscriber',
            name='razorpay_signature',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]

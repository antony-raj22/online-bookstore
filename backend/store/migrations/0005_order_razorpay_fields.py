from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_order_payment_tracking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[('razorpay', 'Razorpay'), ('cod', 'Cash on Delivery')],
                default='razorpay',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='order',
            name='razorpay_payment_id',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='order',
            name='razorpay_signature',
            field=models.CharField(blank=True, max_length=160),
        ),
    ]

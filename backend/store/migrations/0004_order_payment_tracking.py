from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_subscriber_book_genre_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('card', 'Credit / Debit Card'),
                    ('upi', 'UPI'),
                    ('cod', 'Cash on Delivery'),
                ],
                default='card',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('awaiting_payment', 'Awaiting Payment'),
                    ('paid', 'Paid'),
                    ('cod_pending', 'COD Pending'),
                    ('failed', 'Failed'),
                ],
                default='awaiting_payment',
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='tracking_number',
            field=models.CharField(blank=True, max_length=32, null=True, unique=True),
        ),
    ]

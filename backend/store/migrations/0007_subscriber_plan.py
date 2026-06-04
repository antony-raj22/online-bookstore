from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_order_cancellation'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriber',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='subscriber',
            name='plan',
            field=models.CharField(
                choices=[
                    ('monthly', '1 Month'),
                    ('quarterly', '3 Months'),
                    ('yearly', 'Yearly'),
                ],
                default='monthly',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='subscriber',
            name='plan_price',
            field=models.PositiveIntegerField(default=100),
        ),
    ]

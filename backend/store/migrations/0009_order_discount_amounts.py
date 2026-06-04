from django.db import migrations, models


def backfill_order_subtotals(apps, schema_editor):
    Order = apps.get_model('store', 'Order')
    for order in Order.objects.all():
        order.subtotal_amount = order.total_amount
        order.discount_amount = 0
        order.save(update_fields=['subtotal_amount', 'discount_amount'])


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_subscriber_payment_tracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='subtotal_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='order',
            name='discount_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.RunPython(backfill_order_subtotals, migrations.RunPython.noop),
    ]

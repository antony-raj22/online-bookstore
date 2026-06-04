from django.db import migrations
from django.utils import timezone


PLAN_DURATIONS = {
    'monthly': 30,
    'quarterly': 90,
    'yearly': 365,
}


def mark_active_subscribers_paid(apps, schema_editor):
    Subscriber = apps.get_model('store', 'Subscriber')
    for subscriber in Subscriber.objects.filter(is_active=True).exclude(payment_status='paid'):
        subscriber.payment_status = 'paid'
        if subscriber.expires_at is None:
            subscriber.expires_at = timezone.now() + timezone.timedelta(
                days=PLAN_DURATIONS.get(subscriber.plan, 30)
            )
        subscriber.save(update_fields=['payment_status', 'expires_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0012_subscriber_mobile_number'),
    ]

    operations = [
        migrations.RunPython(mark_active_subscribers_paid, migrations.RunPython.noop),
    ]

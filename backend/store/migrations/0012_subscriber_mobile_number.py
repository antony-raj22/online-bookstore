from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0011_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriber',
            name='mobile_number',
            field=models.CharField(blank=True, max_length=20, validators=[django.core.validators.RegexValidator(message='Enter a valid mobile number.', regex='^\\+?[0-9\\s-]{7,20}$')]),
        ),
    ]

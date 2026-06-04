from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Send a test email using the configured Django email backend."

    def add_arguments(self, parser):
        parser.add_argument("to_email", help="Recipient email address for the test message.")

    def handle(self, *args, **options):
        to_email = options["to_email"]
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            raise CommandError("EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are required.")

        sent_count = send_mail(
            subject="BookStore email test",
            message=(
                "This is a test email from BookStore. "
                "If you received this, forgot-password email delivery is working."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )

        if sent_count:
            self.stdout.write(self.style.SUCCESS(f"Test email sent to {to_email}."))
        else:
            raise CommandError("Django did not report a sent email.")

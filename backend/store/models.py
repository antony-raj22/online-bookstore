from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

GENRE_CHOICES = [
    ('fiction',   'Fiction'),
    ('nonfiction','Non-Fiction'),
    ('thriller',  'Thriller'),
    ('scifi',     'Sci-Fi'),
    ('romance',   'Romance'),
    ('biography', 'Biography'),
    ('children',  "Children's"),
    ('academic',  'Academic'),
    ('selfhelp',  'Self-Help'),
    ('art',       'Art & Photography'),
    ('cooking',   'Cooking & Food'),
    ('travel',    'Travel'),
]


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    mobile_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9\s-]{7,20}$',
                message='Enter a valid mobile number.',
            )
        ],
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} profile"


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class Book(models.Model):
    title       = models.CharField(max_length=200)
    author      = models.CharField(max_length=100)
    description = models.TextField()
    price       = models.DecimalField(max_digits=6, decimal_places=2)
    cover_url   = models.URLField(default='https://picsum.photos/id/20/200/300')
    stock       = models.PositiveIntegerField(default=0)
    genre       = models.CharField(max_length=50, choices=GENRE_CHOICES,
                                   default='fiction', blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_new(self):
        return (timezone.now() - self.created_at).days < 30

    def get_genre_display_name(self):
        return dict(GENRE_CHOICES).get(self.genre, self.genre.title())


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('processing', 'Processing'),
        ('shipped',    'Shipped'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('cod', 'Cash on Delivery'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('awaiting_payment', 'Awaiting Payment'),
        ('paid', 'Paid'),
        ('cod_pending', 'COD Pending'),
        ('failed', 'Failed'),
    ]
    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name    = models.CharField(max_length=200)
    address      = models.TextField()
    city         = models.CharField(max_length=100)
    postal_code  = models.CharField(max_length=20)
    created_at   = models.DateTimeField(default=timezone.now)
    paid         = models.BooleanField(default=False)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    stock_reserved = models.BooleanField(default=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                    default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='razorpay')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='awaiting_payment')
    tracking_number = models.CharField(max_length=32, unique=True, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=80, blank=True)
    razorpay_payment_id = models.CharField(max_length=80, blank=True)
    razorpay_signature = models.CharField(max_length=160, blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    @property
    def can_be_cancelled(self):
        return self.status in {'pending', 'processing'}


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    book     = models.ForeignKey(Book, on_delete=models.CASCADE)
    price    = models.DecimalField(max_digits=6, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.book.title}"

    @property
    def line_total(self):
        return self.price * self.quantity


class Subscriber(models.Model):
    PLAN_CHOICES = [
        ('monthly', '1 Month'),
        ('quarterly', '3 Months'),
        ('yearly', 'Yearly'),
    ]
    PLAN_PRICES = {
        'monthly': 100,
        'quarterly': 250,
        'yearly': 900,
    }
    PLAN_DURATIONS = {
        'monthly': 30,
        'quarterly': 90,
        'yearly': 365,
    }
    PAYMENT_STATUS_CHOICES = [
        ('awaiting_payment', 'Awaiting Payment'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    name           = models.CharField(max_length=200, blank=True)
    email          = models.EmailField(unique=True)
    mobile_number  = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9\s-]{7,20}$',
                message='Enter a valid mobile number.',
            )
        ],
    )
    genres         = models.CharField(max_length=500, blank=True,
                                      help_text='Comma-separated genre interests')
    plan           = models.CharField(max_length=20, choices=PLAN_CHOICES, default='monthly')
    plan_price     = models.PositiveIntegerField(default=100)
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='awaiting_payment')
    razorpay_order_id = models.CharField(max_length=80, blank=True)
    razorpay_payment_id = models.CharField(max_length=80, blank=True)
    razorpay_signature = models.CharField(max_length=160, blank=True)
    subscribed_at  = models.DateTimeField(auto_now_add=True)
    expires_at     = models.DateTimeField(blank=True, null=True)
    is_active      = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    @classmethod
    def price_for_plan(cls, plan):
        return cls.PLAN_PRICES.get(plan, cls.PLAN_PRICES['monthly'])

    @classmethod
    def expiry_for_plan(cls, plan):
        return timezone.now() + timezone.timedelta(days=cls.PLAN_DURATIONS.get(plan, 30))

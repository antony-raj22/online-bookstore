from django.db import models
from django.contrib.auth.models import User
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
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
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
    name           = models.CharField(max_length=200, blank=True)
    email          = models.EmailField(unique=True)
    genres         = models.CharField(max_length=500, blank=True,
                                      help_text='Comma-separated genre interests')
    subscribed_at  = models.DateTimeField(auto_now_add=True)
    is_active      = models.BooleanField(default=True)

    def __str__(self):
        return self.email

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

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    book     = models.ForeignKey(Book, on_delete=models.CASCADE)
    price    = models.DecimalField(max_digits=6, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.book.title}"


class Subscriber(models.Model):
    name           = models.CharField(max_length=200, blank=True)
    email          = models.EmailField(unique=True)
    genres         = models.CharField(max_length=500, blank=True,
                                      help_text='Comma-separated genre interests')
    subscribed_at  = models.DateTimeField(auto_now_add=True)
    is_active      = models.BooleanField(default=True)

    def __str__(self):
        return self.email
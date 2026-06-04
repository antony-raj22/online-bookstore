from django.contrib import admin
from django.utils.html import format_html
from .models import Book, Order, OrderItem, Subscriber, UserProfile

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['book']
    extra = 0

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'genre', 'price', 'stock']
    list_editable = ['price', 'stock']
    list_filter = ['genre']
    search_fields = ['title', 'author']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'order_date', 'status', 'payment_status', 'payment_method', 'stock_reserved', 'subtotal_amount', 'discount_amount', 'total_amount', 'colored_status']
    list_display_links = ['id', 'customer_name']
    list_editable = ['status']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'full_name', 'address']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    inlines = [OrderItemInline]

    def customer_name(self, obj):
        return obj.full_name
    customer_name.short_description = 'Customer'

    def order_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    order_date.short_description = 'Order Date'
    order_date.admin_order_field = 'created_at'

    def colored_status(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'shipped': 'purple',
            'delivered': 'green',
            'cancelled': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    colored_status.short_description = 'Status'


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'mobile_number', 'plan', 'plan_price', 'payment_status', 'is_active', 'expires_at', 'subscribed_at']
    list_filter = ['plan', 'payment_status', 'is_active', 'subscribed_at']
    search_fields = ['email', 'name', 'mobile_number', 'genres', 'razorpay_order_id', 'razorpay_payment_id']
    verbose_name = 'Subscribed User'
    verbose_name_plural = 'Subscribed Users'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'display_name', 'email', 'mobile_number', 'updated_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'mobile_number']

    def display_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    display_name.short_description = 'Name'

    def email(self, obj):
        return obj.user.email

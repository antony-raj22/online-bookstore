from django.contrib import admin
from django.utils.html import format_html
from .models import Book, Order, OrderItem, Subscriber

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
    list_display = ['id', 'customer_name', 'order_date', 'status', 'payment_status', 'payment_method', 'total_amount', 'colored_status']
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
    list_display = ['email', 'name', 'is_active', 'subscribed_at']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email', 'name', 'genres']

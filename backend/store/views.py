import base64
import hashlib
import hmac
import json
from urllib import request as urlrequest
from urllib.error import URLError

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import get_random_string

from .forms import AdminBookForm, AdminOrderStatusForm, CancelOrderForm, CheckoutForm, PaymentForm, SubscribeForm, TrackingForm, UserRegisterForm
from .models import Book, GENRE_CHOICES, Order, OrderItem, Subscriber


CATEGORY_META = {
    'fiction': {'name': 'Fiction', 'desc': 'Novels, short stories, literary classics and modern masterpieces.'},
    'nonfiction': {'name': 'Non-Fiction', 'desc': 'History, politics, science, journalism and current affairs.'},
    'thriller': {'name': 'Mystery & Thriller', 'desc': 'Page-turning whodunits, psychological suspense, and crime fiction.'},
    'scifi': {'name': 'Science Fiction', 'desc': 'Space operas, dystopias, hard sci-fi and speculative futures.'},
    'romance': {'name': 'Romance', 'desc': 'Contemporary, historical, paranormal and literary romance.'},
    'biography': {'name': 'Biography & Memoir', 'desc': 'Life stories, autobiographies and inspiring personal journeys.'},
    'children': {'name': "Children's Books", 'desc': 'Picture books, early readers, middle-grade and young adult.'},
    'academic': {'name': 'Academic', 'desc': 'University textbooks, research, reference and study guides.'},
    'selfhelp': {'name': 'Self-Help', 'desc': 'Productivity, mindfulness, finance and personal development.'},
    'art': {'name': 'Art & Photography', 'desc': 'Coffee-table books, design, illustration and visual culture.'},
    'cooking': {'name': 'Cooking & Food', 'desc': 'Recipes, culinary memoirs, nutrition and food culture.'},
    'travel': {'name': 'Travel', 'desc': 'Travel writing, guides, exploration and outdoor adventure.'},
}


def _build_cart_items(cart):
    """Return (cart_items list, total Decimal) from a session cart dict."""
    items, total = [], 0
    for book_id, quantity in cart.items():
        try:
            book = Book.objects.get(id=int(book_id))
        except (Book.DoesNotExist, ValueError):
            continue

        quantity = max(0, min(int(quantity), book.stock))
        if quantity == 0:
            continue
        subtotal = book.price * quantity
        total += subtotal
        items.append({'book': book, 'quantity': quantity, 'subtotal': subtotal})
    return items, total


def _cart_json_payload(cart):
    cart_items, total = _build_cart_items(cart)
    return {
        'items': [
            {
                'book_id': item['book'].id,
                'quantity': item['quantity'],
                'subtotal': f"{item['subtotal']:.2f}",
            }
            for item in cart_items
        ],
        'item_count': sum(item['quantity'] for item in cart_items),
        'line_count': len(cart_items),
        'total': f"{total:.2f}",
    }


def _make_tracking_number(order_id):
    return f"BK{order_id:06d}{get_random_string(4).upper()}"


def _user_can_view_order(user, order):
    return user.is_authenticated and (order.user_id == user.id or user.is_staff)


def _create_razorpay_order(order):
    amount_paise = int(order.total_amount * 100)
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return f"order_demo_{order.id}_{get_random_string(8)}"

    payload = json.dumps({
        'amount': amount_paise,
        'currency': 'INR',
        'receipt': f'bookstore-{order.id}',
        'notes': {'order_id': str(order.id)},
    }).encode('utf-8')
    auth_token = base64.b64encode(
        f'{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}'.encode('utf-8')
    ).decode('ascii')
    api_request = urlrequest.Request(
        'https://api.razorpay.com/v1/orders',
        data=payload,
        headers={
            'Authorization': f'Basic {auth_token}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    with urlrequest.urlopen(api_request, timeout=12) as response:
        data = json.loads(response.read().decode('utf-8'))
    return data['id']


def _verify_razorpay_signature(order_id, payment_id, signature):
    if not settings.RAZORPAY_KEY_SECRET:
        return False
    message = f'{order_id}|{payment_id}'.encode('utf-8')
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
        message,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature or '')


def home(request):
    books = Book.objects.all()
    query = request.GET.get('q')
    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query))
    return render(request, 'store/home.html', {'books': books})


def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    return render(request, 'store/book_detail.html', {'book': book})


def category_list(request):
    slug = request.GET.get('cat', 'all')
    sort = request.GET.get('sort', 'popular')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    books = Book.objects.all()
    if slug and slug != 'all':
        books = books.filter(genre=slug)

    if min_price:
        try:
            books = books.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            books = books.filter(price__lte=float(max_price))
        except ValueError:
            pass

    sort_map = {
        'popular': '-id',
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
    }
    books = books.order_by(sort_map.get(sort, '-id'))

    meta = CATEGORY_META.get(slug, {'name': 'All Books', 'desc': 'Browse our complete collection.'})
    return render(
        request,
        'store/Category.html',
        {
            'books': books,
            'active_cat': slug,
            'category_name': meta['name'],
            'category_desc': meta['desc'],
            'all_categories': CATEGORY_META,
        },
    )


def category_detail(request, slug):
    meta = CATEGORY_META.get(slug, {'name': slug.title(), 'desc': ''})
    sort = request.GET.get('sort', 'popular')
    books = Book.objects.filter(genre=slug)

    sort_map = {
        'popular': '-id',
        'new': '-created_at',
        'price_asc': 'price',
        'price_desc': '-price',
        'az': 'title',
    }
    books = books.order_by(sort_map.get(sort, '-id'))

    return render(
        request,
        'store/Category_detail.html',
        {
            'books': books,
            'category_name': meta['name'],
            'category_desc': meta['desc'],
            'active_slug': slug,
            'all_categories': CATEGORY_META,
        },
    )


def subscribe(request):
    if request.method == 'POST':
        form = SubscribeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            name = form.cleaned_data.get('name', '')
            genres = ','.join(form.cleaned_data.get('genre', []))
            obj, created = Subscriber.objects.get_or_create(
                email=email,
                defaults={'name': name, 'genres': genres},
            )
            if created:
                messages.success(request, "You're subscribed. Check your inbox for 10% off.")
            else:
                if not obj.is_active:
                    obj.is_active = True
                    obj.name = name or obj.name
                    obj.genres = genres or obj.genres
                    obj.save(update_fields=['is_active', 'name', 'genres'])
                messages.info(request, "You're already subscribed. Thanks!")
            return redirect('subscribe')
        messages.error(request, 'Please enter a valid email address.')
    else:
        form = SubscribeForm()
    return render(request, 'store/subscribe.html', {'form': form})


def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if book.stock <= 0:
        messages.warning(request, f'{book.title} is currently out of stock.')
        return redirect('book_detail', book_id=book_id)

    cart = request.session.get('cart', {})
    current_quantity = int(cart.get(str(book_id), 0))
    if current_quantity >= book.stock:
        messages.warning(request, f'Only {book.stock} copy/copies of {book.title} are available.')
        return redirect('book_detail', book_id=book_id)

    cart[str(book_id)] = current_quantity + 1
    request.session['cart'] = cart
    messages.success(request, f'{book.title} added to cart.')
    return redirect('book_detail', book_id=book_id)


@login_required
def buy_now(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if book.stock <= 0:
        messages.warning(request, f'{book.title} is currently out of stock.')
        return redirect('book_detail', book_id=book_id)

    request.session['cart'] = {str(book.id): 1}
    messages.success(request, f'{book.title} is ready for checkout.')
    return redirect('checkout')


def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items, total = _build_cart_items(cart)
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})


def update_cart(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        for key in list(cart.keys()):
            new_qty = request.POST.get(f'quantity_{key}')
            if new_qty is None:
                continue
            try:
                requested_qty = int(new_qty)
                book = Book.objects.get(id=int(key))
            except (ValueError, Book.DoesNotExist):
                cart.pop(key, None)
                continue

            if requested_qty > 0:
                cart[key] = min(requested_qty, book.stock)
            else:
                cart.pop(key, None)

        request.session['cart'] = cart
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(_cart_json_payload(cart))
        messages.success(request, 'Cart updated.')
    return redirect('cart')


def remove_from_cart(request, book_id):
    cart = request.session.get('cart', {})
    if str(book_id) in cart:
        del cart[str(book_id)]
        request.session['cart'] = cart
        messages.success(request, 'Item removed from cart.')
    return redirect('cart')


@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('home')

    cart_items, total = _build_cart_items(cart)
    if not cart_items:
        request.session['cart'] = {}
        messages.warning(request, 'The items in your cart are no longer available.')
        return redirect('cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                locked_books = {
                    book.id: book
                    for book in Book.objects.select_for_update().filter(id__in=[item['book'].id for item in cart_items])
                }
                for item in cart_items:
                    book = locked_books[item['book'].id]
                    if item['quantity'] > book.stock:
                        messages.error(request, f'Not enough stock available for {book.title}.')
                        return redirect('cart')

                order = Order.objects.create(
                    user=request.user,
                    full_name=form.cleaned_data['full_name'],
                    address=form.cleaned_data['address'],
                    city=form.cleaned_data['city'],
                    postal_code=form.cleaned_data['postal_code'],
                    total_amount=total,
                    paid=False,
                    payment_method=form.cleaned_data['payment_method'],
                    payment_status='cod_pending' if form.cleaned_data['payment_method'] == 'cod' else 'awaiting_payment',
                    status='pending',
                )
                for item in cart_items:
                    book = locked_books[item['book'].id]
                    OrderItem.objects.create(
                        order=order,
                        book=book,
                        price=book.price,
                        quantity=item['quantity'],
                    )
                    book.stock -= item['quantity']
                    book.save(update_fields=['stock'])

            request.session['pending_order_id'] = order.id
            if order.payment_method == 'cod':
                order.tracking_number = _make_tracking_number(order.id)
                order.save(update_fields=['tracking_number'])
                request.session['cart'] = {}
                messages.success(request, 'Order placed successfully. Pay when your books arrive.')
                return redirect('bill', order_id=order.id)

            messages.info(request, 'Delivery details saved. Complete payment to confirm your order.')
            return redirect('payment', order_id=order.id)
    else:
        form = CheckoutForm()

    return render(request, 'store/checkout.html', {'form': form, 'cart_items': cart_items, 'total': total})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__book').order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__book'), id=order_id, user=request.user)
    if request.method != 'POST':
        return redirect('order_history')

    form = CancelOrderForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Please enter a reason before cancelling the order.')
        return redirect('order_history')

    if not order.can_be_cancelled:
        messages.error(request, 'This order can no longer be cancelled.')
        return redirect('order_history')

    with transaction.atomic():
        locked_order = (
            Order.objects.select_for_update()
            .prefetch_related('items__book')
            .get(id=order.id, user=request.user)
        )
        if not locked_order.can_be_cancelled:
            messages.error(request, 'This order can no longer be cancelled.')
            return redirect('order_history')

        for item in locked_order.items.select_related('book'):
            item.book.stock += item.quantity
            item.book.save(update_fields=['stock'])

        locked_order.status = 'cancelled'
        locked_order.cancellation_reason = form.cleaned_data['reason'].strip()
        locked_order.cancelled_at = timezone.now()
        locked_order.save(update_fields=['status', 'cancellation_reason', 'cancelled_at'])

    messages.success(request, f'Order #{order.id} has been cancelled.')
    return redirect('order_history')


@login_required
def payment(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__book'), id=order_id)
    if not _user_can_view_order(request.user, order):
        messages.error(request, 'You cannot access that payment page.')
        return redirect('order_history')
    if order.status == 'cancelled':
        messages.error(request, 'This order has been cancelled and cannot be paid.')
        return redirect('order_history')
    if order.paid or order.payment_method == 'cod':
        return redirect('bill', order_id=order.id)

    if request.method == 'POST':
        razorpay_order_id = request.POST.get('razorpay_order_id', order.razorpay_order_id)
        razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_signature = request.POST.get('razorpay_signature', '')
        demo_payment = request.POST.get('demo_payment') == '1'

        if demo_payment and not settings.RAZORPAY_KEY_ID:
            is_valid_payment = True
            razorpay_payment_id = f'pay_demo_{get_random_string(10)}'
        else:
            is_valid_payment = _verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

        if is_valid_payment:
            order.paid = True
            order.payment_status = 'paid'
            order.status = 'processing'
            order.tracking_number = order.tracking_number or _make_tracking_number(order.id)
            order.razorpay_order_id = razorpay_order_id
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.save(update_fields=[
                'paid', 'payment_status', 'status', 'tracking_number',
                'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature',
            ])
            request.session['cart'] = {}
            request.session.pop('pending_order_id', None)
            messages.success(request, 'Payment complete. Your order has been placed successfully.')
            return redirect('bill', order_id=order.id)

        order.payment_status = 'failed'
        order.save(update_fields=['payment_status'])
        messages.error(request, 'Razorpay payment verification failed. Please try again.')
        return redirect('payment', order_id=order.id)

    if not order.razorpay_order_id:
        try:
            order.razorpay_order_id = _create_razorpay_order(order)
            order.save(update_fields=['razorpay_order_id'])
        except (URLError, TimeoutError, KeyError, ValueError) as exc:
            messages.error(request, f'Could not start Razorpay payment: {exc}')

    return render(
        request,
        'store/payment.html',
        {
            'order': order,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'razorpay_amount': int(order.total_amount * 100),
            'razorpay_currency': 'INR',
            'demo_payment_enabled': not settings.RAZORPAY_KEY_ID,
        },
    )


@login_required
def bill(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__book'), id=order_id)
    if not _user_can_view_order(request.user, order):
        messages.error(request, 'You cannot access that bill.')
        return redirect('order_history')
    return render(request, 'store/bill.html', {'order': order})


def track_order(request):
    form = TrackingForm(request.GET or None)
    order = None
    if form.is_valid():
        order = (
            Order.objects.prefetch_related('items__book')
            .filter(id=form.cleaned_data['order_id'], postal_code__iexact=form.cleaned_data['postal_code'].strip())
            .first()
        )
        if not order:
            messages.error(request, 'No order matched those details. Check the order number and postal code.')
    return render(request, 'store/track_order.html', {'form': form, 'order': order})


@login_required
@user_passes_test(lambda user: user.is_staff)
def staff_dashboard(request):
    book_form = AdminBookForm()
    order_form = AdminOrderStatusForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_book':
            book_form = AdminBookForm(request.POST)
            if book_form.is_valid():
                book_form.save()
                messages.success(request, 'Book added.')
                return redirect('staff_dashboard')
        elif action == 'update_book':
            book = get_object_or_404(Book, id=request.POST.get('book_id'))
            book_form = AdminBookForm(request.POST, instance=book)
            if book_form.is_valid():
                book_form.save()
                messages.success(request, 'Book updated.')
                return redirect('staff_dashboard')
        elif action == 'delete_book':
            book = get_object_or_404(Book, id=request.POST.get('book_id'))
            book.delete()
            messages.success(request, 'Book deleted.')
            return redirect('staff_dashboard')
        elif action == 'update_order':
            order = get_object_or_404(Order, id=request.POST.get('order_id'))
            order_form = AdminOrderStatusForm(request.POST, instance=order)
            if order_form.is_valid():
                order_form.save()
                messages.success(request, 'Order updated.')
                return redirect('staff_dashboard')
        elif action == 'toggle_subscriber':
            subscriber = get_object_or_404(Subscriber, id=request.POST.get('subscriber_id'))
            subscriber.is_active = not subscriber.is_active
            subscriber.save(update_fields=['is_active'])
            messages.success(request, 'Subscriber updated.')
            return redirect('staff_dashboard')

    totals = Order.objects.aggregate(revenue=Sum('total_amount'), orders=Count('id'))
    recent_orders = Order.objects.select_related('user').prefetch_related('items__book').order_by('-created_at')[:12]
    low_stock_books = Book.objects.filter(stock__lte=5).order_by('stock', 'title')[:8]
    context = {
        'total_orders': totals['orders'] or 0,
        'total_revenue': totals['revenue'] or 0,
        'book_count': Book.objects.count(),
        'subscriber_count': Subscriber.objects.filter(is_active=True).count(),
        'books': Book.objects.order_by('-created_at')[:20],
        'recent_orders': recent_orders,
        'low_stock_books': low_stock_books,
        'subscribers': Subscriber.objects.order_by('-subscribed_at')[:12],
        'status_counts': Order.objects.values('status').annotate(count=Count('id')).order_by('status'),
        'book_form': book_form,
        'order_form': order_form,
        'order_status_choices': Order.STATUS_CHOICES,
        'payment_status_choices': Order.PAYMENT_STATUS_CHOICES,
    }
    return render(request, 'store/admin_dashboard.html', context)


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Welcome, {user.first_name or user.username}!')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'store/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(request.GET.get('next', 'home'))
        messages.error(request, 'Invalid username or password. Please try again.')
    return render(request, 'store/login.html')


def user_logout(request):
    logout(request)
    messages.success(request, "You've been logged out. See you soon!")
    return redirect('home')

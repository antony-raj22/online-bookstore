import base64
import hashlib
import hmac
import json
from decimal import Decimal
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

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
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import AdminBookForm, AdminOrderStatusForm, CancelOrderForm, CheckoutForm, PaymentForm, SubscribeForm, TrackingForm, UserRegisterForm
from .models import Book, GENRE_CHOICES, Order, OrderItem, Subscriber, UserProfile


SUBSCRIBED_USER_DISCOUNT_RATE = Decimal('0.10')


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
                'book': _book_payload(item['book']),
                'quantity': item['quantity'],
                'subtotal': f"{item['subtotal']:.2f}",
            }
            for item in cart_items
        ],
        'item_count': sum(item['quantity'] for item in cart_items),
        'line_count': len(cart_items),
        'total': f"{total:.2f}",
    }


def _book_payload(book):
    return {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'description': book.description,
        'price': f"{book.price:.2f}",
        'cover_url': book.cover_url,
        'stock': book.stock,
        'genre': book.genre,
        'genre_label': book.get_genre_display_name(),
        'is_new': book.is_new,
    }


def _category_payload(slug, meta):
    return {
        'slug': slug,
        'name': meta['name'],
        'description': meta['desc'],
    }


def _json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _active_subscription_for_user(user):
    if not user.is_authenticated:
        return None

    now = timezone.now()
    profile = UserProfile.objects.filter(user=user).first()
    mobile_number = profile.mobile_number.strip() if profile else ''
    user_email = user.email.strip() if user.email else ''
    normalized_mobile = ''.join(char for char in mobile_number if char.isdigit())

    if not user_email and not normalized_mobile:
        return None

    active_subscribers = (
        Subscriber.objects.filter(is_active=True, payment_status='paid')
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gte=now))
        .order_by('-expires_at', '-subscribed_at')
    )

    for subscriber in active_subscribers:
        subscriber_mobile = ''.join(char for char in subscriber.mobile_number if char.isdigit())
        if user_email and subscriber.email.lower() == user_email.lower():
            return subscriber
        if normalized_mobile and subscriber_mobile == normalized_mobile:
            return subscriber
    return None


def _subscription_initial_for_user(user):
    if not user.is_authenticated:
        return {}

    profile = getattr(user, 'profile', None)
    return {
        'name': user.get_full_name() or user.username,
        'email': user.email,
        'mobile_number': getattr(profile, 'mobile_number', ''),
    }


def _subscription_success_redirect(request):
    if request.session.get('cart'):
        return redirect('checkout')
    return redirect('subscribe')


def _discount_for_subscribed_user(user, subtotal):
    subscriber = _active_subscription_for_user(user)
    if not subscriber:
        return None, Decimal('0.00'), subtotal

    discount = (subtotal * SUBSCRIBED_USER_DISCOUNT_RATE).quantize(Decimal('0.01'))
    return subscriber, discount, subtotal - discount


def _order_has_reserved_stock(order):
    return order.stock_reserved


def _make_tracking_number(order_id):
    return f"BK{order_id:06d}{get_random_string(4).upper()}"


def _user_can_view_order(user, order):
    return user.is_authenticated and (order.user_id == user.id or user.is_staff)


def _create_razorpay_order(order):
    amount_paise = int(order.total_amount * 100)
    return _create_razorpay_payment_order(
        amount_paise=amount_paise,
        receipt=f'bookstore-{order.id}',
        notes={'order_id': str(order.id)},
        demo_prefix=f'order_demo_{order.id}',
    )


def _create_razorpay_payment_order(amount_paise, receipt, notes, demo_prefix):
    if _razorpay_demo_enabled():
        return f"{demo_prefix}_{get_random_string(8)}"

    payload = json.dumps({
        'amount': amount_paise,
        'currency': 'INR',
        'receipt': receipt,
        'notes': notes,
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


def _razorpay_demo_enabled():
    return not (settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)


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


def _book_card_line(book):
    stock_text = f"{book.stock} in stock" if book.stock else "currently out of stock"
    return (
        f"- [{book.title}](/book/{book.id}/) by {book.author} "
        f"- Rs.{book.price} - {book.get_genre_display_name()} - {stock_text}"
    )


def _search_support_books(message, limit=5):
    normalized = message.lower().replace('sci-fi', 'scifi').replace('non-fiction', 'nonfiction')
    stopwords = {
        'book', 'books', 'recommend', 'recommendation', 'suggest', 'show',
        'find', 'please', 'want', 'need', 'best', 'good',
    }
    words = [
        word.strip(".,!?;:#").lower()
        for word in normalized.replace('-', ' ').split()
        if len(word.strip(".,!?;:#")) >= 3 and word.strip(".,!?;:#").lower() not in stopwords
    ]
    if not words:
        return []
    genre_values = {value: label.lower() for value, label in GENRE_CHOICES}
    genre_query = Q()
    text_query = Q()
    matched_genre = False

    for value, label in genre_values.items():
        if value in words or any(part in words for part in label.replace("&", " ").replace("-", " ").split()):
            genre_query |= Q(genre=value)
            matched_genre = True

    for word in words:
        text_query |= (
            Q(title__icontains=word)
            | Q(author__icontains=word)
            | Q(description__icontains=word)
        )

    books = Book.objects.all()
    if matched_genre:
        books = books.filter(genre_query)
    elif text_query:
        books = books.filter(text_query)
    return list(books.order_by('-stock', 'price', 'title')[:limit])


def _support_order_response(request, message):
    if not any(word in message for word in ['order', 'track', 'tracking', 'delivered', 'shipped', 'cancel']):
        return ''

    if not request.user.is_authenticated:
        return (
            "Please sign in to view your orders. After login, ask **Where is my order?** "
            "or use [Track Order](/track-order/) with your order number and postal code."
        )

    orders = list(
        Order.objects.filter(user=request.user)
        .prefetch_related('items__book')
        .order_by('-created_at')[:5]
    )
    if not orders:
        return "I could not find any orders on your account yet. You can start from the [book catalog](/)."

    requested_order = None
    for token in message.replace('#', ' ').split():
        if token.isdigit():
            requested_order = next((order for order in orders if order.id == int(token)), None)
            break

    selected = [requested_order] if requested_order else orders[:3]
    lines = ["Here is your order information:"]
    for order in selected:
        item_names = ', '.join(item.book.title for item in order.items.all()[:3]) or 'Books'
        tracking = order.tracking_number or 'Tracking number will appear after confirmation.'
        cancel_note = (
            f" You can cancel it from [My Orders](/order-history/) while it is {order.get_status_display().lower()}."
            if order.can_be_cancelled else ''
        )
        lines.append(
            f"- **Order #{order.id}**: {order.get_status_display()} / "
            f"{order.get_payment_status_display()} / Rs.{order.total_amount}. "
            f"Items: {item_names}. Tracking: {tracking}.{cancel_note}"
        )
    return "\n".join(lines)


def _support_subscription_response(message):
    if not any(word in message for word in ['subscribe', 'subscription', 'plan', 'monthly', 'yearly', 'billing']):
        return ''
    return (
        "BookStore subscription plans:\n"
        "- **1 Month**: Rs.100\n"
        "- **3 Months**: Rs.250\n"
        "- **Yearly**: Rs.900\n\n"
        "After payment, your account becomes **subscribed** and you get **10% off book orders** "
        "when your login email matches the subscribed email. You can choose a plan at "
        "[Subscribe](/subscribe/). Payment is handled securely with Razorpay."
    )


def _support_policy_response(message):
    if any(word in message for word in ['privacy', 'data', 'policy']):
        return (
            "**Privacy Policy**\n"
            "We use your information only to process orders, personalize your experience, "
            "and send updates you request."
        )
    if any(word in message for word in ['terms', 'return', 'refund']):
        return (
            "**Terms of Service**\n"
            "Please provide accurate order details and follow the store purchase and return policies. "
            "For billing or order help, contact support@bookstore.com."
        )
    if any(word in message for word in ['contact', 'help', 'support', 'email']):
        return "You can contact support at [support@bookstore.com](mailto:support@bookstore.com)."
    return ''


def _local_support_reply(request, message):
    lowered = message.lower()
    if any(word in lowered for word in ['discount', 'subscribed', 'subscriber', 'member deal', '10%']):
        subscriber = _active_subscription_for_user(request.user)
        if subscriber:
            return (
                f"Your account is **subscribed** on the {subscriber.get_plan_display()} plan. "
                "A **10% discount** will be applied automatically at checkout while the subscription is active."
            )
        return (
            "The **10% discount** is only for subscribed users. Subscribe with the same email as your account, "
            "complete payment, then sign in and checkout to receive the discount automatically."
        )

    response = _support_order_response(request, lowered)
    if response:
        return response

    response = _support_subscription_response(lowered)
    if response:
        return response

    response = _support_policy_response(lowered)
    if response:
        return response

    books = _search_support_books(message)
    if books:
        lines = ["I found these books for you:"]
        lines.extend(_book_card_line(book) for book in books)
        lines.append("\nWant a different mood or category? Try **romance**, **thriller**, **academic**, or **self-help**.")
        return "\n".join(lines)

    if any(word in lowered for word in ['hi', 'hello', 'hey']):
        return (
            "Hi, I am the BookStore support assistant. I can recommend books, explain subscriptions, "
            "help track orders, and answer store policy questions."
        )

    return (
        "I can help with book recommendations, order tracking, subscriptions, payments, and store policies. "
        "Try asking **Recommend Sci-Fi books**, **Where is my order?**, or **What are the subscription plans?**"
    )


def _support_context(request, message):
    books = _search_support_books(message)
    orders = []
    if request.user.is_authenticated:
        orders = list(
            Order.objects.filter(user=request.user)
            .prefetch_related('items__book')
            .order_by('-created_at')[:5]
        )
    return {
        'user': request.user.username if request.user.is_authenticated else 'guest',
        'subscribed_user_discount_percent': 10,
        'active_subscription': bool(_active_subscription_for_user(request.user)),
        'books': [
            {
                'title': book.title,
                'author': book.author,
                'genre': book.get_genre_display_name(),
                'price': str(book.price),
                'stock': book.stock,
                'url': f'/book/{book.id}/',
            }
            for book in books
        ],
        'orders': [
            {
                'id': order.id,
                'status': order.get_status_display(),
                'payment_status': order.get_payment_status_display(),
                'tracking_number': order.tracking_number,
                'total': str(order.total_amount),
                'can_cancel': order.can_be_cancelled,
                'items': [item.book.title for item in order.items.all()],
            }
            for order in orders
        ],
        'subscription_plans': Subscriber.PLAN_PRICES,
    }


def _gemini_support_reply(request, message):
    if not settings.GEMINI_API_KEY:
        return ''

    context = _support_context(request, message)
    prompt = (
        "You are BookStore's customer support assistant. Answer briefly in friendly markdown. "
        "Use only the supplied store context for books, orders, subscriptions, and policies. "
        "Explain that only active paid subscribed users receive the automatic 10% book-order discount. "
        "Never invent an order or tracking number. If a user asks to cancel an order, explain whether it can be "
        "cancelled and direct them to /order-history/.\n\n"
        f"Store context:\n{json.dumps(context, ensure_ascii=True)}\n\n"
        f"Customer message: {message}"
    )
    payload = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.4, 'maxOutputTokens': 700},
    }).encode('utf-8')
    api_url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}'
    )
    api_request = urlrequest.Request(
        api_url,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urlrequest.urlopen(api_request, timeout=12) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (HTTPError, URLError, TimeoutError, KeyError, ValueError):
        return ''

    candidates = data.get('candidates') or []
    if not candidates:
        return ''
    parts = candidates[0].get('content', {}).get('parts', [])
    return ''.join(part.get('text', '') for part in parts).strip()


@require_POST
def support_chat(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid message payload.'}, status=400)

    message = str(payload.get('message', '')).strip()
    if not message:
        return JsonResponse({'error': 'Please enter a message.'}, status=400)

    reply = _gemini_support_reply(request, message)
    source = 'gemini' if reply else 'local'
    if not reply:
        reply = _local_support_reply(request, message)

    return JsonResponse({
        'reply': reply,
        'source': source,
        'suggestions': [
            'Recommend Sci-Fi books',
            'Recommend Academic books',
            'Track my order',
            'Subscription plans',
            'Cancel an order',
            'Contact support',
        ],
    })


@ensure_csrf_cookie
def api_bootstrap(request):
    active_subscription = _active_subscription_for_user(request.user)
    return JsonResponse({
        'user': {
            'is_authenticated': request.user.is_authenticated,
            'is_staff': request.user.is_staff if request.user.is_authenticated else False,
            'name': request.user.get_full_name() or request.user.username if request.user.is_authenticated else '',
            'email': request.user.email if request.user.is_authenticated else '',
            'is_subscribed': bool(active_subscription),
        },
        'cart': _cart_json_payload(request.session.get('cart', {})),
        'categories': [_category_payload(slug, meta) for slug, meta in CATEGORY_META.items()],
    })


def api_books(request):
    books = Book.objects.all()
    query = request.GET.get('q', '').strip()
    genre = request.GET.get('genre', '').strip()
    availability = request.GET.get('availability', '').strip()
    sort = request.GET.get('sort', 'newest').strip()

    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(author__icontains=query)
            | Q(description__icontains=query)
        )
    if genre:
        books = books.filter(genre=genre)
    if availability == 'in_stock':
        books = books.filter(stock__gt=0)
    elif availability == 'new':
        books = books.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))

    sort_map = {
        'newest': '-created_at',
        'price_low': 'price',
        'price_high': '-price',
        'title': 'title',
        'stock': '-stock',
    }
    books = books.order_by(sort_map.get(sort, '-created_at'))
    return JsonResponse({
        'books': [_book_payload(book) for book in books],
        'filters': {
            'query': query,
            'genre': genre,
            'availability': availability,
            'sort': sort,
        },
    })


def api_book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    related_books = list(Book.objects.filter(genre=book.genre).exclude(id=book.id).order_by('-created_at')[:4])
    if not related_books:
        related_books = list(Book.objects.exclude(id=book.id).order_by('-created_at')[:4])
    return JsonResponse({
        'book': _book_payload(book),
        'related_books': [_book_payload(related) for related in related_books],
    })


def api_categories(request):
    categories = []
    counts = dict(Book.objects.values_list('genre').annotate(total=Count('id')))
    for slug, meta in CATEGORY_META.items():
        category = _category_payload(slug, meta)
        category['book_count'] = counts.get(slug, 0)
        categories.append(category)
    return JsonResponse({'categories': categories})


def api_cart(request):
    return JsonResponse(_cart_json_payload(request.session.get('cart', {})))


@require_POST
def api_add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if book.stock <= 0:
        return JsonResponse({'error': f'{book.title} is currently out of stock.'}, status=400)

    cart = request.session.get('cart', {})
    current_quantity = int(cart.get(str(book_id), 0))
    if current_quantity >= book.stock:
        return JsonResponse({'error': f'Only {book.stock} copy/copies of {book.title} are available.'}, status=400)

    cart[str(book_id)] = current_quantity + 1
    request.session['cart'] = cart
    payload = _cart_json_payload(cart)
    payload['message'] = f'{book.title} added to cart.'
    return JsonResponse(payload)


@require_POST
def api_update_cart(request):
    cart = request.session.get('cart', {})
    body = _json_body(request)
    updates = body.get('items', body)

    if isinstance(updates, list):
        updates = {
            str(item.get('book_id')): item.get('quantity')
            for item in updates
            if isinstance(item, dict) and item.get('book_id') is not None
        }

    if not isinstance(updates, dict):
        return JsonResponse({'error': 'Send a JSON object of book_id to quantity.'}, status=400)

    for raw_book_id, raw_quantity in updates.items():
        key = str(raw_book_id)
        try:
            requested_qty = int(raw_quantity)
            book = Book.objects.get(id=int(key))
        except (TypeError, ValueError, Book.DoesNotExist):
            cart.pop(key, None)
            continue

        if requested_qty > 0:
            cart[key] = min(requested_qty, book.stock)
        else:
            cart.pop(key, None)

    request.session['cart'] = cart
    return JsonResponse(_cart_json_payload(cart))


@require_POST
def api_remove_from_cart(request, book_id):
    cart = request.session.get('cart', {})
    cart.pop(str(book_id), None)
    request.session['cart'] = cart
    return JsonResponse(_cart_json_payload(cart))


def home(request):
    books = Book.objects.all()
    query = request.GET.get('q', '').strip()
    genre = request.GET.get('genre', '').strip()
    availability = request.GET.get('availability', '').strip()
    sort = request.GET.get('sort', 'newest').strip()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(description__icontains=query)
        )
    if genre:
        books = books.filter(genre=genre)
    if availability == 'in_stock':
        books = books.filter(stock__gt=0)
    elif availability == 'new':
        books = books.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))

    sort_map = {
        'newest': '-created_at',
        'price_low': 'price',
        'price_high': '-price',
        'title': 'title',
        'stock': '-stock',
    }
    books = books.order_by(sort_map.get(sort, '-created_at'))

    return render(
        request,
        'store/home.html',
        {
            'books': books,
            'all_genres': GENRE_CHOICES,
            'active_genre': genre,
            'active_availability': availability,
            'active_sort': sort,
            'search_query': query,
        },
    )


def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    related_books = list(Book.objects.filter(genre=book.genre).exclude(id=book.id).order_by('-created_at')[:4])
    if not related_books:
        related_books = Book.objects.exclude(id=book.id).order_by('-created_at')[:4]
    return render(request, 'store/book_detail.html', {'book': book, 'related_books': related_books})


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
    active_subscription = _active_subscription_for_user(request.user)
    subscribed_genres = []
    days_remaining = None
    if active_subscription:
        days_remaining = None
        if active_subscription.expires_at:
            days_remaining = max((active_subscription.expires_at - timezone.now()).days, 0)
        subscribed_genres = [
            dict(GENRE_CHOICES).get(genre, genre.title())
            for genre in active_subscription.genres.split(',')
            if genre
        ]

    if request.method == 'POST':
        form = SubscribeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            name = form.cleaned_data.get('name', '')
            mobile_number = form.cleaned_data['mobile_number'].strip()
            plan = form.cleaned_data['plan']
            genres = ','.join(form.cleaned_data.get('genre', []))
            subscriber, created = Subscriber.objects.get_or_create(
                email=email,
                defaults={
                    'name': name,
                    'mobile_number': mobile_number,
                    'genres': genres,
                    'plan': plan,
                    'plan_price': Subscriber.price_for_plan(plan),
                    'payment_status': 'awaiting_payment',
                    'is_active': False,
                },
            )
            if not created:
                subscriber.name = name or subscriber.name
                subscriber.mobile_number = mobile_number
                subscriber.genres = genres or subscriber.genres
                subscriber.plan = plan
                subscriber.plan_price = Subscriber.price_for_plan(plan)
                subscriber.payment_status = 'awaiting_payment'
                subscriber.is_active = False
                subscriber.razorpay_order_id = ''
                subscriber.razorpay_payment_id = ''
                subscriber.razorpay_signature = ''
                subscriber.save(update_fields=[
                    'name', 'mobile_number', 'genres', 'plan', 'plan_price', 'payment_status', 'is_active',
                    'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature',
                ])
            messages.info(request, 'Complete Razorpay payment to activate your subscription.')
            return redirect('subscription_payment', subscriber_id=subscriber.id)
        messages.error(request, 'Please check the subscription details and try again.')
    else:
        initial = _subscription_initial_for_user(request.user)
        if active_subscription:
            initial.update({
                'name': active_subscription.name,
                'email': active_subscription.email,
                'mobile_number': active_subscription.mobile_number,
                'plan': active_subscription.plan,
                'genre': [genre for genre in active_subscription.genres.split(',') if genre],
            })
        form = SubscribeForm(initial=initial)
    return render(
        request,
        'store/subscribe.html',
        {
            'form': form,
            'active_subscription': active_subscription,
            'days_remaining': days_remaining,
            'has_expiry': active_subscription.expires_at is not None if active_subscription else False,
            'subscribed_genres': subscribed_genres,
        },
    )


def subscription_payment(request, subscriber_id):
    subscriber = get_object_or_404(Subscriber, id=subscriber_id)

    if request.method == 'POST':
        razorpay_order_id = request.POST.get('razorpay_order_id', subscriber.razorpay_order_id)
        razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_signature = request.POST.get('razorpay_signature', '')
        demo_payment = request.POST.get('demo_payment') == '1'

        if demo_payment and _razorpay_demo_enabled():
            is_valid_payment = True
            razorpay_payment_id = f'pay_demo_sub_{get_random_string(10)}'
        else:
            is_valid_payment = _verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

        if is_valid_payment:
            subscriber.is_active = True
            subscriber.payment_status = 'paid'
            subscriber.expires_at = Subscriber.expiry_for_plan(subscriber.plan)
            subscriber.razorpay_order_id = razorpay_order_id
            subscriber.razorpay_payment_id = razorpay_payment_id
            subscriber.razorpay_signature = razorpay_signature
            subscriber.save(update_fields=[
                'is_active', 'payment_status', 'expires_at',
                'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature',
            ])
            messages.success(
                request,
                f'{subscriber.get_plan_display()} subscription activated for Rs.{subscriber.plan_price}.',
            )
            return _subscription_success_redirect(request)

        subscriber.payment_status = 'failed'
        subscriber.save(update_fields=['payment_status'])
        messages.error(request, 'Razorpay payment verification failed. Please try again.')
        return redirect('subscription_payment', subscriber_id=subscriber.id)

    if subscriber.is_active and subscriber.payment_status == 'paid':
        messages.info(request, 'This subscription is already active.')
        return redirect('subscribe')

    if not subscriber.razorpay_order_id:
        try:
            subscriber.razorpay_order_id = _create_razorpay_payment_order(
                amount_paise=subscriber.plan_price * 100,
                receipt=f'subscription-{subscriber.id}',
                notes={
                    'subscriber_id': str(subscriber.id),
                    'email': subscriber.email,
                    'mobile_number': subscriber.mobile_number,
                    'plan': subscriber.plan,
                },
                demo_prefix=f'sub_demo_{subscriber.id}',
            )
            subscriber.save(update_fields=['razorpay_order_id'])
        except (URLError, TimeoutError, KeyError, ValueError) as exc:
            messages.error(request, f'Could not start Razorpay payment: {exc}')

    return render(
        request,
        'store/subscription_payment.html',
        {
            'subscriber': subscriber,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'razorpay_amount': subscriber.plan_price * 100,
            'razorpay_currency': 'INR',
            'demo_payment_enabled': _razorpay_demo_enabled(),
            'payment_ready': bool(subscriber.razorpay_order_id),
        },
    )


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
    active_subscriber, discount_amount, payable_total = _discount_for_subscribed_user(request.user, total)
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
                    subtotal_amount=total,
                    discount_amount=discount_amount,
                    total_amount=payable_total,
                    stock_reserved=form.cleaned_data['payment_method'] == 'cod',
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
                    if order.payment_method == 'cod':
                        book.stock -= item['quantity']
                        book.save(update_fields=['stock'])

            request.session['pending_order_id'] = order.id
            if order.payment_method == 'cod':
                order.tracking_number = _make_tracking_number(order.id)
                order.save(update_fields=['tracking_number'])
                request.session['cart'] = {}
                messages.success(request, 'Order placed successfully. Pay when your books arrive.')
                return redirect('bill', order_id=order.id)

            messages.info(request, 'Razorpay order created. Complete payment to confirm your order.')
            return redirect('payment', order_id=order.id)
    else:
        form = CheckoutForm()

    return render(
        request,
        'store/checkout.html',
        {
            'form': form,
            'cart_items': cart_items,
            'subtotal': total,
            'discount_amount': discount_amount,
            'total': payable_total,
            'active_subscriber': active_subscriber,
        },
    )


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

        if _order_has_reserved_stock(locked_order):
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

        if demo_payment and _razorpay_demo_enabled():
            is_valid_payment = True
            razorpay_payment_id = f'pay_demo_{get_random_string(10)}'
        else:
            is_valid_payment = _verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

        if is_valid_payment:
            with transaction.atomic():
                locked_order = (
                    Order.objects.select_for_update()
                    .prefetch_related('items__book')
                    .get(id=order.id)
                )
                if locked_order.status == 'cancelled':
                    messages.error(request, 'This order has been cancelled and cannot be paid.')
                    return redirect('order_history')

                if not locked_order.stock_reserved:
                    for item in locked_order.items.select_related('book'):
                        book = Book.objects.select_for_update().get(id=item.book_id)
                        if item.quantity > book.stock:
                            locked_order.payment_status = 'failed'
                            locked_order.save(update_fields=['payment_status'])
                            messages.error(
                                request,
                                f'Not enough stock available for {book.title}. Your order is not confirmed.',
                            )
                            return redirect('order_history')

                    for item in locked_order.items.select_related('book'):
                        book = Book.objects.select_for_update().get(id=item.book_id)
                        book.stock -= item.quantity
                        book.save(update_fields=['stock'])

                locked_order.paid = True
                locked_order.payment_status = 'paid'
                locked_order.status = 'processing'
                locked_order.stock_reserved = True
                locked_order.tracking_number = locked_order.tracking_number or _make_tracking_number(locked_order.id)
                locked_order.razorpay_order_id = razorpay_order_id
                locked_order.razorpay_payment_id = razorpay_payment_id
                locked_order.razorpay_signature = razorpay_signature
                locked_order.save(update_fields=[
                    'paid', 'payment_status', 'status', 'stock_reserved', 'tracking_number',
                    'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature',
                ])
            request.session['cart'] = {}
            request.session.pop('pending_order_id', None)
            messages.success(request, 'Payment complete. Your order is now confirmed.')
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
            'demo_payment_enabled': _razorpay_demo_enabled(),
        },
    )


@login_required
def bill(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__book'), id=order_id)
    if not _user_can_view_order(request.user, order):
        messages.error(request, 'You cannot access that bill.')
        return redirect('order_history')
    if order.payment_method == 'razorpay' and not order.paid:
        messages.warning(request, 'Complete Razorpay payment before viewing the bill. This order is not confirmed yet.')
        return redirect('payment', order_id=order.id)
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
            update_fields = ['is_active']
            if subscriber.is_active:
                subscriber.payment_status = 'paid'
                subscriber.expires_at = subscriber.expires_at or Subscriber.expiry_for_plan(subscriber.plan)
                update_fields.extend(['payment_status', 'expires_at'])
            subscriber.save(update_fields=update_fields)
            messages.success(request, 'Subscriber updated.')
            return redirect('staff_dashboard')

    totals = Order.objects.aggregate(revenue=Sum('total_amount'), orders=Count('id'))
    recent_orders = Order.objects.select_related('user').prefetch_related('items__book').order_by('-created_at')[:12]
    book_query = request.GET.get('book_q', '').strip()
    book_genre = request.GET.get('book_genre', '').strip()
    books = Book.objects.all()
    if book_query:
        books = books.filter(Q(title__icontains=book_query) | Q(author__icontains=book_query))
    if book_genre:
        books = books.filter(genre=book_genre)
    books = books.order_by('title')
    low_stock_queryset = Book.objects.filter(stock__lte=5)
    low_stock_books = low_stock_queryset.order_by('stock', 'title')[:8]
    context = {
        'total_orders': totals['orders'] or 0,
        'total_revenue': totals['revenue'] or 0,
        'book_count': Book.objects.count(),
        'subscriber_count': Subscriber.objects.filter(is_active=True).count(),
        'low_stock_count': low_stock_queryset.count(),
        'books': books[:60],
        'book_search_query': book_query,
        'book_search_genre': book_genre,
        'book_result_count': books.count(),
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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Book, Order, OrderItem, Subscriber, GENRE_CHOICES
from .forms import UserRegisterForm, CheckoutForm, SubscribeForm

# ── helpers ──────────────────────────────────────────────────
CATEGORY_META = {
    'fiction':   {'name': 'Fiction',           'icon': '📖', 'desc': 'Novels, short stories, literary classics and modern masterpieces.'},
    'nonfiction':{'name': 'Non-Fiction',        'icon': '🔬', 'desc': 'History, politics, science, journalism and current affairs.'},
    'thriller':  {'name': 'Mystery & Thriller', 'icon': '🔪', 'desc': 'Page-turning whodunits, psychological suspense, and crime fiction.'},
    'scifi':     {'name': 'Science Fiction',    'icon': '🚀', 'desc': 'Space operas, dystopias, hard sci-fi and speculative futures.'},
    'romance':   {'name': 'Romance',            'icon': '💌', 'desc': 'Contemporary, historical, paranormal and literary romance.'},
    'biography': {'name': 'Biography & Memoir', 'icon': '🏆', 'desc': 'Life stories, autobiographies and inspiring personal journeys.'},
    'children':  {'name': "Children's Books",   'icon': '🧸', 'desc': 'Picture books, early readers, middle-grade and young adult.'},
    'academic':  {'name': 'Academic',           'icon': '🎓', 'desc': 'University textbooks, research, reference and study guides.'},
    'selfhelp':  {'name': 'Self-Help',          'icon': '💡', 'desc': 'Productivity, mindfulness, finance and personal development.'},
    'art':       {'name': 'Art & Photography',  'icon': '🎨', 'desc': 'Coffee-table books, design, illustration and visual culture.'},
    'cooking':   {'name': 'Cooking & Food',     'icon': '🍳', 'desc': 'Recipes, culinary memoirs, nutrition and food culture.'},
    'travel':    {'name': 'Travel',             'icon': '✈️', 'desc': 'Travel writing, guides, exploration and outdoor adventure.'},
}

def _build_cart_items(cart):
    """Return (cart_items list, total Decimal) from session cart dict."""
    items, total = [], 0
    for book_id, quantity in cart.items():
        try:
            book = Book.objects.get(id=int(book_id))
            subtotal = book.price * quantity
            total   += subtotal
            items.append({'book': book, 'quantity': quantity, 'subtotal': subtotal})
        except Book.DoesNotExist:
            pass
    return items, total

# ── public views ──────────────────────────────────────────────

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
    """All-categories browsing page with sidebar filters."""
    slug   = request.GET.get('cat', 'all')
    sort   = request.GET.get('sort', 'popular')
    min_p  = request.GET.get('min_price')
    max_p  = request.GET.get('max_price')

    books = Book.objects.all()

    # Filter by genre
    if slug and slug != 'all':
        books = books.filter(genre=slug)

    # Filter by price
    if min_p:
        try: books = books.filter(price__gte=float(min_p))
        except ValueError: pass
    if max_p:
        try: books = books.filter(price__lte=float(max_p))
        except ValueError: pass

    # Sort
    sort_map = {
        'popular':    '-id',
        'price_asc':  'price',
        'price_desc': '-price',
        'newest':     '-created_at',
    }
    books = books.order_by(sort_map.get(sort, '-id'))

    meta = CATEGORY_META.get(slug, {'name': 'All Books', 'icon': '📚',
                                     'desc': 'Browse our complete collection.'})
    return render(request, 'store/Category.html', {
        'books':         books,
        'active_cat':    slug,
        'category_name': meta['name'],
        'category_icon': meta['icon'],
        'category_desc': meta['desc'],
        'all_categories': CATEGORY_META,
    })


def category_detail(request, slug):
    """Books filtered by a specific category slug."""
    meta  = CATEGORY_META.get(slug, {'name': slug.title(), 'icon': '📚', 'desc': ''})
    sort  = request.GET.get('sort', 'popular')
    books = Book.objects.filter(genre=slug)

    sort_map = {
        'popular':    '-id',
        'new':        '-created_at',
        'price_asc':  'price',
        'price_desc': '-price',
        'az':         'title',
    }
    books = books.order_by(sort_map.get(sort, '-id'))

    return render(request, 'store/Category_detail.html', {
        'books':         books,
        'category_name': meta['name'],
        'category_icon': meta['icon'],
        'category_desc': meta['desc'],
        'active_slug':   slug,
    })


def subscribe(request):
    if request.method == 'POST':
        form = SubscribeForm(request.POST)
        if form.is_valid():
            email  = form.cleaned_data['email']
            name   = form.cleaned_data.get('name', '')
            genres = ','.join(form.cleaned_data.get('genre', []))
            obj, created = Subscriber.objects.get_or_create(
                email=email,
                defaults={'name': name, 'genres': genres}
            )
            if created:
                messages.success(request, '🎉 You\'re subscribed! Check your inbox for 10% off.')
            else:
                messages.info(request, 'You\'re already subscribed — thanks!')
            return redirect('subscribe')
        else:
            messages.error(request, 'Please enter a valid email address.')
    else:
        form = SubscribeForm()
    return render(request, 'store/subscribe.html', {'form': form})


# ── cart views ────────────────────────────────────────────────

def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    cart = request.session.get('cart', {})
    cart[str(book_id)] = cart.get(str(book_id), 0) + 1
    request.session['cart'] = cart
    messages.success(request, f'✓ <strong>{book.title}</strong> added to cart.')
    return redirect('book_detail', book_id=book_id)


def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items, total = _build_cart_items(cart)
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})


def update_cart(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        for key in list(cart.keys()):
            new_qty = request.POST.get(f'quantity_{key}')
            if new_qty is not None:
                try:
                    new_qty = int(new_qty)
                    if new_qty > 0:
                        cart[key] = new_qty
                    else:
                        del cart[key]
                except ValueError:
                    pass
        request.session['cart'] = cart
        messages.success(request, 'Cart updated.')
    return redirect('cart')


def remove_from_cart(request, book_id):
    cart = request.session.get('cart', {})
    if str(book_id) in cart:
        del cart[str(book_id)]
        request.session['cart'] = cart
        messages.success(request, 'Item removed from cart.')
    return redirect('cart')


# ── checkout & orders ─────────────────────────────────────────

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('home')

    cart_items, total = _build_cart_items(cart)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user         = request.user,
                full_name    = form.cleaned_data['full_name'],
                address      = form.cleaned_data['address'],
                city         = form.cleaned_data['city'],
                postal_code  = form.cleaned_data['postal_code'],
                total_amount = total,
                paid         = True,
            )
            for item in cart_items:
                OrderItem.objects.create(
                    order    = order,
                    book     = item['book'],
                    price    = item['book'].price,
                    quantity = item['quantity'],
                )
                item['book'].stock = max(0, item['book'].stock - item['quantity'])
                item['book'].save()

            request.session['cart'] = {}
            messages.success(request, '🎉 Order placed successfully! Thank you.')
            return redirect('order_history')
    else:
        form = CheckoutForm()

    return render(request, 'store/checkout.html', {
        'form':       form,
        'cart_items': cart_items,
        'total':      total,
    })


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})


# ── auth views ────────────────────────────────────────────────

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user,
                  backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Welcome, {user.first_name or user.username}! 🎉')
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
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    return render(request, 'store/login.html')


def user_logout(request):
    logout(request)
    messages.success(request, 'You\'ve been logged out. See you soon!')
    return redirect('home')
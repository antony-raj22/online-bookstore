from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Book, Order, OrderItem
from .forms import UserRegisterForm, CheckoutForm

def home(request):
    books = Book.objects.all()
    query = request.GET.get('q')
    if query:
        books = books.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        )
    return render(request, 'store/home.html', {'books': books})

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    return render(request, 'store/book_detail.html', {'book': book})

def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    cart = request.session.get('cart', {})
    cart[str(book_id)] = cart.get(str(book_id), 0) + 1
    request.session['cart'] = cart
    messages.success(request, f'Added {book.title} to cart.')
    return redirect('book_detail', book_id=book_id)

def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for book_id, quantity in cart.items():
        book = Book.objects.get(id=int(book_id))
        subtotal = book.price * quantity
        total += subtotal
        cart_items.append({
            'book': book,
            'quantity': quantity,
            'subtotal': subtotal,
        })
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})

def update_cart(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        for key in list(cart.keys()):
            new_qty = request.POST.get(f'quantity_{key}')
            if new_qty:
                new_qty = int(new_qty)
                if new_qty > 0:
                    cart[key] = new_qty
                else:
                    del cart[key]
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

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('home')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Calculate total
            total = 0
            cart_items_data = []
            for book_id, quantity in cart.items():
                book = Book.objects.get(id=int(book_id))
                subtotal = book.price * quantity
                total += subtotal
                cart_items_data.append((book, quantity, book.price))
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                full_name=form.cleaned_data['full_name'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                postal_code=form.cleaned_data['postal_code'],
                total_amount=total,
                paid=True  # Simulate payment
            )
            for book, quantity, price in cart_items_data:
                OrderItem.objects.create(
                    order=order,
                    book=book,
                    price=price,
                    quantity=quantity
                )
                # Reduce stock
                book.stock -= quantity
                book.save()
            
            # Clear cart
            request.session['cart'] = {}
            messages.success(request, 'Order placed successfully!')
            return redirect('order_history')
    else:
        form = CheckoutForm()
    return render(request, 'store/checkout.html', {'form': form, 'cart': cart})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful.')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'store/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        from django.contrib.auth import authenticate
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Logged in successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials.')
    return render(request, 'store/login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out.')
    return redirect('home')
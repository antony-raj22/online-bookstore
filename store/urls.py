from django.urls import path, include
from . import views

urlpatterns = [
    # Home & books
    path('',                           views.home,             name='home'),
    path('book/<int:book_id>/',        views.book_detail,      name='book_detail'),

    # Cart
    path('add-to-cart/<int:book_id>/', views.add_to_cart,      name='add_to_cart'),
    path('cart/',                      views.view_cart,         name='cart'),
    path('update-cart/',               views.update_cart,       name='update_cart'),
    path('remove-from-cart/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Checkout & orders
    path('checkout/',                  views.checkout,          name='checkout'),
    path('order-history/',             views.order_history,     name='order_history'),

    # Categories
    path('categories/',                views.category_list,     name='category_list'),
    path('category/<str:slug>/',       views.category_detail,   name='category_detail'),

    # Subscribe
    path('subscribe/',                 views.subscribe,         name='subscribe'),

    # Auth
    path('register/',                  views.register,          name='register'),
    path('login/',                     views.user_login,        name='login'),
    path('logout/',                    views.user_logout,       name='logout'),

    # Social auth (requires social-auth-app-django)
    path('auth/',                      include('social_django.urls', namespace='social')),
]
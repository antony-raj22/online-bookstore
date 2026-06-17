from django.contrib.auth import views as auth_views
from django.urls import path, include
from . import views

urlpatterns = [
    # React/API frontend
    path('api/bootstrap/',             views.api_bootstrap,    name='api_bootstrap'),
    path('api/books/',                 views.api_books,        name='api_books'),
    path('api/books/<int:book_id>/',   views.api_book_detail,  name='api_book_detail'),
    path('api/categories/',            views.api_categories,   name='api_categories'),
    path('api/cart/',                  views.api_cart,         name='api_cart'),
    path('api/cart/add/<int:book_id>/', views.api_add_to_cart, name='api_add_to_cart'),
    path('api/cart/update/',           views.api_update_cart,  name='api_update_cart'),
    path('api/cart/remove/<int:book_id>/', views.api_remove_from_cart, name='api_remove_from_cart'),

    # Home & books
    path('',                           views.home,             name='home'),
    path('book/<int:book_id>/',        views.book_detail,      name='book_detail'),

    # Cart
    path('add-to-cart/<int:book_id>/', views.add_to_cart,      name='add_to_cart'),
    path('buy-now/<int:book_id>/',     views.buy_now,          name='buy_now'),
    path('cart/',                      views.view_cart,         name='cart'),
    path('update-cart/',               views.update_cart,       name='update_cart'),
    path('remove-from-cart/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Checkout & orders
    path('checkout/',                  views.checkout,          name='checkout'),
    path('payment/<int:order_id>/',     views.payment,           name='payment'),
    path('bill/<int:order_id>/',        views.bill,              name='bill'),
    path('track-order/',               views.track_order,       name='track_order'),
    path('order-history/',             views.order_history,     name='order_history'),
    path('order/<int:order_id>/cancel/', views.cancel_order,     name='cancel_order'),
    path('staff-dashboard/',           views.staff_dashboard,   name='staff_dashboard'),
    path('support/chat/',              views.support_chat,      name='support_chat'),

    # Categories
    path('categories/',                views.category_list,     name='category_list'),
    path('category/<str:slug>/',       views.category_detail,   name='category_detail'),

    # Subscribe
    path('subscribe/',                 views.subscribe,         name='subscribe'),
    path('subscribe/payment/<int:subscriber_id>/', views.subscription_payment, name='subscription_payment'),

    # Auth
    path('register/',                  views.register,          name='register'),
    path('login/',                     views.user_login,        name='login'),
    path('logout/',                    views.user_logout,       name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        from_email=None,
        success_url='/password-reset/done/',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/reset/done/',
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),

    # Social auth (requires social-auth-app-django)
    path('auth/',                      include('social_django.urls', namespace='social')),
]

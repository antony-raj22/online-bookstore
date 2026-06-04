def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(cart.values())
    return {'cart_count': count}


def social_auth_status(request):
    from django.conf import settings

    return {
        'social_auth_available': {
            'google': bool(settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY and settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET),
            'facebook': bool(settings.SOCIAL_AUTH_FACEBOOK_KEY and settings.SOCIAL_AUTH_FACEBOOK_SECRET),
            'github': bool(settings.SOCIAL_AUTH_GITHUB_KEY and settings.SOCIAL_AUTH_GITHUB_SECRET),
        }
    }


def account_details(request):
    if not request.user.is_authenticated:
        return {'account_details': None, 'active_subscription': None, 'is_subscribed_user': False}

    from django.db.models import Q
    from django.utils import timezone
    from .models import Subscriber, UserProfile

    profile, _created = UserProfile.objects.get_or_create(user=request.user)
    user_email = request.user.email.strip() if request.user.email else ''
    mobile_number = profile.mobile_number.strip()
    normalized_mobile = ''.join(char for char in mobile_number if char.isdigit())
    active_subscription = None

    if user_email or normalized_mobile:
        active_subscribers = (
            Subscriber.objects.filter(is_active=True, payment_status='paid')
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now()))
            .order_by('-expires_at', '-subscribed_at')
        )
        for subscriber in active_subscribers:
            subscriber_mobile = ''.join(char for char in subscriber.mobile_number if char.isdigit())
            if user_email and subscriber.email.lower() == user_email.lower():
                active_subscription = subscriber
                break
            if normalized_mobile and subscriber_mobile == normalized_mobile:
                active_subscription = subscriber
                break

    return {
        'account_details': {
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'mobile_number': profile.mobile_number,
        },
        'active_subscription': active_subscription,
        'is_subscribed_user': active_subscription is not None,
    }

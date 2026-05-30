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

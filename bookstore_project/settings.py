from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-72b8^j02h&*gv8x(0r@k!@vw5#$h5&*z=2&@5!#r9z%=^%1@x*'

DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
    # Social auth — install with: pip install social-auth-app-django
    'social_django',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Social auth middleware
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'bookstore_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom cart counter
                'store.context_processors.cart_count',
                # Social auth
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.github.GithubOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME':   BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

LOGIN_URL           = 'login'
LOGIN_REDIRECT_URL  = 'home'
LOGOUT_REDIRECT_URL = 'home'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── SOCIAL AUTH KEYS ─────────────────────────────────────────
# Replace these with your actual credentials from each provider's developer console.

# Google: https://console.cloud.google.com/
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY    = 'YOUR_GOOGLE_CLIENT_ID'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'YOUR_GOOGLE_CLIENT_SECRET'

# Facebook: https://developers.facebook.com/
SOCIAL_AUTH_FACEBOOK_KEY         = 'YOUR_FACEBOOK_APP_ID'
SOCIAL_AUTH_FACEBOOK_SECRET      = 'YOUR_FACEBOOK_APP_SECRET'
SOCIAL_AUTH_FACEBOOK_SCOPE       = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {'fields': 'id,name,email'}

# GitHub: https://github.com/settings/developers
SOCIAL_AUTH_GITHUB_KEY           = 'YOUR_GITHUB_CLIENT_ID'
SOCIAL_AUTH_GITHUB_SECRET        = 'YOUR_GITHUB_CLIENT_SECRET'
SOCIAL_AUTH_GITHUB_SCOPE         = ['user:email']

SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
]
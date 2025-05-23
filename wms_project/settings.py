from pathlib import Path
import os

# ----------------------------
# Base Directory and Security
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-3jg^20w1f=-ks%&)%ksz8)icft!!b-kwh!-5_6=ua_txt3j%*@'
DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "travel-safe-wms.onrender.com",
    "wms.travelsafe.net",
]

# ----------------------------
# Installed Applications
# ----------------------------
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inventory',
    'rest_framework',
    'widget_tweaks',
]

# ----------------------------
# Middleware
# ----------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'wms_project.urls'

# ----------------------------
# Templates
# ----------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'wms_project.wsgi.application'

# ----------------------------
# Database
# ----------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ----------------------------
# Password Validation
# ----------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ----------------------------
# Localization
# ----------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ----------------------------
# Static Files
# ----------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----------------------------
# Django REST Framework
# ----------------------------
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ]
}

# ----------------------------
# Jazzmin Admin Configuration
# ----------------------------
JAZZMIN_SETTINGS = {
    "site_title": "Travel Safe Admin",
    "site_header": "Travel Safe WMS",
    "site_brand": "Travel Safe",
    "site_logo": "img/travel_safe_logo.png",
    "welcome_sign": "Welcome to Travel Safe Admin Portal",
    "copyright": "Travel Safe",
    "search_model": "auth.User",
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": ["auth", "inventory"],
    "custom_links": {},
    "icons": {
        "auth": "fas fa-users-cog",
        "inventory.Item": "fas fa-boxes",
        "inventory.Bin": "fas fa-box-open",
        "inventory.Location": "fas fa-warehouse",
        "inventory.InventoryMovement": "fas fa-dolly",
    },
    "show_ui_builder": False,
    "dark_mode_theme": None,
    "language_chooser": False,
}

# ----------------------------
# Login/Logout Redirects
# ----------------------------
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ----------------------------
# eBay OAuth API Integration
# ----------------------------
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID", "TravelSa-TravelSa-PRD-3a70f81c3-b1e944ab")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET", "")  # ✅ Store this in Render ENV settings
EBAY_REDIRECT_URI = "https://travel-safe-wms.onrender.com/auth/ebay/return/"
EBAY_ACCESS_TOKEN = "v^1.1#i^1#r^0#I^3#p^3#f^0#t^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"  # ✅ Your full token here
EBAY_REFRESH_TOKEN = "v^1.1#i^1#r^1#I^3#p^3#f^0#t^Ul4xMF81OkRCOTY4RjM3MzJEN0EwNEY0NDUwRkMwRjU5RjkzNjI1XzFfMSNFXjI2MA=="

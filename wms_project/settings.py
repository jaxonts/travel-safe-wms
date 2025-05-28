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
EBAY_ACCESS_TOKEN = "v^1.1#i^1#r^0#f^0#I^3#p^3#t^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"  # ✅ Your full token here
EBAY_REFRESH_TOKEN = "v^1.1#i^1#r^1#p^3#I^3#f^0#t^Ul4xMF80OkMyRkM1MkQzN0M3NUZEMTg4Mjc0QjFEOEE1NEJGQUZDXzFfMSNFXjI2MA=="
EBAY_BASE64_ENCODED_CREDENTIALS = "VHJhdmVsU2EtVHJhdmVsU2EtUFJELTNhNzBmODFjMy1iMWU5NDRhYjpQUkQtYTcwZjgxYzMxMDM1LTBkNWYtNGI1YS1hYTQ3LTNiMDE="

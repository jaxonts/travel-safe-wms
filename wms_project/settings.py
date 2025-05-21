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
EBAY_ACCESS_TOKEN = "v^1.1#i^1#I^3#f^0#r^0#p^3#t^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"  # ✅ Your full token here
EBAY_REFRESH_TOKEN = "v^1.1#i^1#I^3#r^1#f^0#p^3#t^Ul4xMF80OkQ5OTJBRkNCQUNFNzU1QkUxNUM1MzVFRDg0NzVFQUU1XzFfMSNFXjI2MA==", "")

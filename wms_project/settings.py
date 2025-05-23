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
EBAY_ACCESS_TOKEN = "v^1.1#i^1#p^3#f^0#r^0#I^3#t^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"  # ✅ Your full token here
EBAY_REFRESH_TOKEN = "v^1.1#i^1#r^1#f^0#I^3#p^3#t^Ul4xMF84OkVGMDE1OTgyMEY0MTdCNEU2NTg2NTcwQUJGQjJFMUY2XzFfMSNFXjI2MA=="

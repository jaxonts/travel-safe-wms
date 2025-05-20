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
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID", "TravelSa-TravelSa-PRD-3a70f81c3-ble944ab")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET", "")  # ✅ Store this in Render ENV settings
EBAY_REDIRECT_URI = "https://travel-safe-wms.onrender.com/auth/ebay/return/"
EBAY_ACCESS_TOKEN = "v^1.1#i^1#f^0#r^0#p^3#I^3#t^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"  # ✅ Your full token here

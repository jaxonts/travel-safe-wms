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

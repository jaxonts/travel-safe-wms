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
EBAY_ACCESS_TOKEN = "v^1.1#i^1#I^3#p^3#f^0#r^0#t^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"  # ✅ Your full token here
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN", "")
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN", "")

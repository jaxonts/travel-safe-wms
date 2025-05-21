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
EBAY_ACCESS_TOKEN = "v^1.1#i^1#f^0#r^0#p^3#I^3#t^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"  # ✅ Your full token here
EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN", "")

from pathlib import Path
import os

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
# Installed apps
# ----------------------------
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',  # ✅ fixed typo
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inventory',
    'rest_framework',
    'widget_tweaks',  # ✅ Required for 'add_class' in templates
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
# Password validation
# ----------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ----------------------------
# Internationalization
# ----------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ----------------------------
# Static files
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
# Jazzmin Admin Customization
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
# Authentication redirects
# ----------------------------
LOGIN_REDIRECT_URL = '/admin/'  # ✅ Directs all successful logins here
LOGOUT_REDIRECT_URL = '/accounts/login/'

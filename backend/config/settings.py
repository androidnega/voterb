import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-change-this-in-production!')
# Production: export DEBUG=0 (or False). Console SMS fallback is only allowed when DEBUG is True.
DEBUG = os.environ.get('DEBUG', 'True').strip().lower() in ('1', 'true', 'yes', 'on')

# Comma-separated hosts, e.g. localhost,127.0.0.1,192.168.1.10
# Set LAN_DEV=1 via scripts/lan-dev.sh to allow any host on your local network.
if os.environ.get('LAN_DEV') == '1':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [
        h.strip() for h in os.environ.get(
            'ALLOWED_HOSTS',
            'localhost,127.0.0.1',
        ).split(',') if h.strip()
    ]

LAN_ORIGIN = os.environ.get('LAN_ORIGIN', '').strip()
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'https://localhost:5173',
    'https://127.0.0.1:5173',
]
if LAN_ORIGIN:
    origin = LAN_ORIGIN.rstrip('/')
    CSRF_TRUSTED_ORIGINS.append(origin)
    # Trust both http and https for the same LAN host (dev camera needs https)
    if origin.startswith('http://'):
        CSRF_TRUSTED_ORIGINS.append('https://' + origin[len('http://'):])
    elif origin.startswith('https://'):
        CSRF_TRUSTED_ORIGINS.append('http://' + origin[len('https://'):])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'corsheaders',
    'channels',
    # Local apps
    'accounts',
    'elections',
    'candidates',
    'voting',
    'security',
    'results',
    'strongroom',
    'fraud',
    'notifications',
    'ussd',
    'system',
    'operations',
    'audit',
    'dashboard',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'uuid',
    'USER_ID_CLAIM': 'user_uuid',
}

CORS_ALLOW_ALL_ORIGINS = True

# Redis powers live monitor fan-out, Celery broker/result backend, and SMS prewarm cache.
# Set REDIS_URL (e.g. redis://127.0.0.1:6379/0). Falls back to in-memory for local/dev.
REDIS_URL = (os.environ.get('REDIS_URL') or '').strip()
USE_REDIS = bool(REDIS_URL) and os.environ.get('USE_REDIS', '1') != '0'

if USE_REDIS:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'KEY_PREFIX': 'voterb',
            'TIMEOUT': 300,
        },
    }
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [REDIS_URL],
                'capacity': 5000,
                'expiry': 30,
            },
        },
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'voterb-local',
        },
    }
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# Celery — SMS + background jobs. Broker prefers REDIS_URL, then CELERY_BROKER_URL.
CELERY_BROKER_URL = (
    os.environ.get('CELERY_BROKER_URL')
    or REDIS_URL
    or 'redis://127.0.0.1:6379/1'
).strip()
CELERY_RESULT_BACKEND = (
    os.environ.get('CELERY_RESULT_BACKEND')
    or REDIS_URL
    or CELERY_BROKER_URL
).strip()
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 60
CELERY_TASK_SOFT_TIME_LIMIT = 45
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_DEFAULT_QUEUE = 'votebridge'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Accra'
# When workers are down, critical SMS still sends in-process (see notifications.tasks).
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_TASK_ALWAYS_EAGER', '0').strip().lower() in (
    '1', 'true', 'yes', 'on',
)
CELERY_WORKER_CONCURRENCY = max(1, int(os.environ.get('CELERY_WORKER_CONCURRENCY', '6') or 6))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

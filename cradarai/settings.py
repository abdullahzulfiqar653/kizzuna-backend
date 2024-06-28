"""
Django settings for cradarai project.

Generated by 'django-admin startproject' using Django 4.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from datetime import timedelta
from pathlib import Path

import environ
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

env = environ.Env()
# reading .env file
environ.Env.read_env(".env")
environ.Env.read_env(".env.example")
os.environ["OPENAI_API_KEY"] = env("OPENAI_API_KEY")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = env("GOOGLE_APPLICATION_CREDENTIALS")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", cast=bool)

ALLOWED_HOSTS = env("ALLOWED_HOSTS", cast=list)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.kizunna\.com/?$",
    r"^https://\w+\.raijin\.ai/?$",
    "http://localhost:5173",
]
FRONTEND_URL = env("FRONTEND_URL")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "api",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
    "ordered_model",
    "storages",
    "django_cleanup",  # To delete the file when the model instance that contains the file is deleted.
    "django_celery_results",
]

MIDDLEWARE = [
    "easy_health_check.middleware.HealthCheckMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": [
        "api.permissions.IsOwnerEditorOrViewerReadOnly",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
        "api.filters.backends.QueryFilter",
    ],
    "NON_FIELD_ERRORS_KEY": "detail",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Raijin Backend API",
    "DESCRIPTION": "API description",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/",
    "ENUM_NAME_OVERRIDES": {  # This is to suppress warnings related to enum
        "NoteSentiment": "api.models.note.Note.Sentiment",
    },
}

SIMPLE_JWT = {
    "ROTATE_REFRESH_TOKENS": True,
    "UPDATE_LAST_LOGIN": True,
    "TOKEN_OBTAIN_SERIALIZER": "api.serializers.auth.CustomTokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "api.serializers.auth.CustomTokenRefreshSerializer",
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# Set SESSION_ENGINE to 'django.contrib.sessions.backends.db' for database-backed sessions
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Optional: Set SESSION_EXPIRE_AT_BROWSER_CLOSE to True to expire the session when the user closes the browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

ROOT_URLCONF = "cradarai.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "api" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cradarai.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("MASTER_DB_NAME"),
        "USER": env("MASTER_DB_USERNAME"),
        "PASSWORD": env("MASTER_DB_PASSWORD"),
        "HOST": env("MASTER_DB_HOST"),
        "PORT": env("MASTER_DB_PORT"),
        "ATOMIC_REQUESTS": True,
    },
}

AUTH_USER_MODEL = "api.User"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [os.path.join(BASE_DIR, "translations")]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

USE_S3 = env("USE_S3", cast=bool, default=False)
if USE_S3 is True:
    # Set your AWS credentials and region. You can also store these in environment variables.# AWS_ACCESS_KEY_ID = 'access_key'
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_QUERYSTRING_AUTH = True
    default_storage_backend = "api.storage_backends.PrivateMediaStorage"
else:
    MEDIA_URL = "media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
    default_storage_backend = "django.core.files.storage.FileSystemStorage"

FILE_UPLOAD_HANDLERS = ["django.core.files.uploadhandler.TemporaryFileUploadHandler"]
STORAGES = {
    "default": {
        "BACKEND": default_storage_backend,
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_USE_TLS = env("EMAIL_USE_TLS", cast=bool)
EMAIL_USE_SSL = env("EMAIL_USE_SSL", cast=bool)
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

LOGGING = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": [
                "console",
            ],
            "level": "INFO",
        },
    },
}


def traces_sampler(ctx):
    # Don't trace requests to health endpoint
    if ctx.get("wsgi_environ", {}).get("PATH_INFO", "") == "/health/":
        return 0
    else:
        return 1


sentry_sdk.init(
    dsn=env("SENTRY_DSN", default=""),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    enable_tracing=True,
    environment=env("SENTRY_ENV"),
    integrations=[CeleryIntegration(monitor_beat_tasks=True)],
    traces_sampler=traces_sampler,
)

INVITATION_LINK_TIMEOUT = 3 * 24 * 60 * 60  # 3 days

# Optional: You can also set a different location for your static files within the bucket.
# STATICFILES_LOCATION = 'static'
# STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATICFILES_LOCATION}/'

FILTERS_NULL_CHOICE_LABEL = "null"

# To make the link rendered by django https
# Ref: https://stackoverflow.com/a/59071836/9577282
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# Celery config
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"

# App Quotas
DURATION_MINUTE_SINGLE_FILE = env("DURATION_MINUTE_SINGLE_FILE", cast=int)
DURATION_MINUTE_WORKSPACE = env("DURATION_MINUTE_WORKSPACE", cast=int)
STORAGE_GB_WORKSPACE = env("STORAGE_GB_WORKSPACE", cast=int)

# Health check settings
DJANGO_EASY_HEALTH_CHECK = {
    "PATH": "/health/",
    "RETURN_STATUS_CODE": 200,
    "RETURN_BYTE_DATA": "Success",
}

# Slack Credentials
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI")

# Demo project settings
DEMO_PROJECT_ID = env("DEMO_PROJECT_ID", default=None)
DEMO_USER_ID = env("DEMO_USER_ID", default=None)

MIXPANEL_TOKEN = env("MIXPANEL_TOKEN")

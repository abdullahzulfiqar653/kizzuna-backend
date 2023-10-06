"""
Django settings for cradarai project.

Generated by 'django-admin startproject' using Django 4.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path

import environ

env = environ.Env()
# reading .env file
environ.Env.read_env('.env')
os.environ['OPENAI_API_KEY'] = env('OPENAI_API_KEY')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)&p#ue*_uiab=o7hfwx7u&_e#4oi(gfpj7f-wc+15mdv_!!=dh'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', cast=bool)

ALLOWED_HOSTS = env('ALLOWED_HOSTS', cast=list)
FRONTEND_URL = env('FRONTEND_URL')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'user',
    'workspace',
    'project',
    'note',
    'tag',
    'takeaway',
    'transcriber',
    'rest_framework',
    'corsheaders',
    'drf_yasg',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

SIMPLE_JWT = {
    "ROTATE_REFRESH_TOKENS": True,
    "TOKEN_OBTAIN_SERIALIZER": "api.serializers.CustomTokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "api.serializers.CustomTokenRefreshSerializer",
}

# Set SESSION_ENGINE to 'django.contrib.sessions.backends.db' for database-backed sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Optional: Set SESSION_EXPIRE_AT_BROWSER_CLOSE to True to expire the session when the user closes the browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

ROOT_URLCONF = 'cradarai.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'web_app' / 'templates', 
            BASE_DIR / 'auth' / 'templates'
            ],
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

WSGI_APPLICATION = 'cradarai.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('MASTER_DB_NAME'),
        'USER': env('MASTER_DB_USERNAME'),
        'PASSWORD': env('MASTER_DB_PASSWORD'),
        'HOST': env('MASTER_DB_HOST'),
        'PORT': env('MASTER_DB_PORT'),
        'ATOMIC_REQUESTS': True,
        'OPTIONS': {
            'sql_mode': 'STRICT_TRANS_TABLES',
        },
    },
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ORIGIN_ALLOW_ALL = True  # Allow requests from any origin, change it to a specific domain in production

# Set your AWS credentials and region. You can also store these in environment variables.# AWS_ACCESS_KEY_ID = 'access_key'
# AWS_ACCESS_KEY_ID = 'access_key'
# AWS_SECRET_ACCESS_KEY = 'secret_key'
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_DEFAULT_ACL = env('AWS_DEFAULT_ACL')  # Set the access control list for uploaded files
AWS_QUERYSTRING_AUTH = env('AWS_QUERYSTRING_AUTH', cast=bool)  # This will prevent the S3 signature from being included in the URL
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME')  # e.g., 'us-west-1'

# Set the S3 domain to use for serving media files. You can use the default S3 domain or set up a custom one.
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# Set the location where media files will be uploaded within the bucket.
# This is optional but can help you organize files within your bucket.
MEDIAFILES_LOCATION = 'media'
# MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/'
MEDIA_URL = env('MEDIA_URL')

# To test with local storage
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_USE_TLS = env('EMAIL_USE_TLS', cast=bool)
EMAIL_USE_SSL = env('EMAIL_USE_SSL', cast=bool)
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
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

INVITATION_LINK_TIMEOUT = 3 * 24 * 60 * 60 # 3 days

# Optional: You can also set a different location for your static files within the bucket.
# STATICFILES_LOCATION = 'static'
# STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATICFILES_LOCATION}/'
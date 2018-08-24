"""
Django settings for api project.

Generated by 'django-admin startproject' using Django 2.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import datetime

import local_settings
from corsheaders.defaults import default_headers

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = local_settings.SECRET_KEY

CACHE_DIR = os.path.join(BASE_DIR, 'cache')

SITE_DOMAIN = local_settings.SITE_DOMAIN
SUBDOMAIN_NAME = local_settings.SUPER_GAME_SUBDOMAIN_NAME

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = local_settings.DEBUG

ALLOWED_HOSTS = local_settings.ALLOWED_HOSTS
VERIFY_SIGNATURE = local_settings.VERIFY_SIGNATURE

# 下注影响因素，影响赔率变化
BET_FACTOR = 0.9

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_jwt',
    'rest_framework.authtoken',
    'rest_framework_filters',
    'mptt',
    'captcha',
    'rolepermissions',
    'corsheaders',
    'channels',
    'base',
    'utils',

    'users',
    'wc_auth',
    'quiz',
    'guess',
    'setting',
    'sms',
    'config',
    'chat',
    'reversion',
    'spider',
    'console',
    'handle',
    'marksix',
    # 'recharge',
    # 'silk',
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
    'base.middleware.RequestExceptionHandler',
    # 'silk.middleware.SilkyMiddleware',
]

ROOT_URLCONF = 'api.urls'

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

WSGI_APPLICATION = 'api.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': local_settings.DB
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'EXCEPTION_HANDLER': 'base.exceptions.wc_exception_handler',
}

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=2592000),  # 一个月时间
}

AUTHENTICATION_BACKENDS = ("utils.custom_backend.UsernameOrIdCardBackend",)
# CAPTCHA
IS_CAPTCHA_ENABLE = True
# 是否开启用户注册登录图形验证码
IS_USER_CAPTCHA_ENABLE = local_settings.IS_USER_CAPTCHA_ENABLE
CLUB_REVENUE = local_settings.CLUB_REVENUE
EXCHANGE = local_settings.EXCHANGE
GSG_EXCHANGE_DATE = local_settings.GSG_EXCHANGE_DATE
GSG_EXCHANGE_START_DATE = local_settings.GSG_EXCHANGE_START_DATE
ETH_ONCE_EXCHANGE_LOWER_LIMIT = local_settings.ETH_ONCE_EXCHANGE_LOWER_LIMIT
ETH_EXCHANGE_INSTRUCTION_ONE = local_settings.ETH_EXCHANGE_INSTRUCTION_ONE
ETH_EXCHANGE_INSTRUCTION_TWO = local_settings.ETH_EXCHANGE_INSTRUCTION_TWO
ETH_EXCHANGE_INSTRUCTION_THREE = local_settings.ETH_EXCHANGE_INSTRUCTION_THREE
ETH_EXCHANGE_INSTRUCTION_ONE_FOUR = local_settings.ETH_EXCHANGE_INSTRUCTION_ONE_FOUR

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = (
    '*'
)
CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'VIEW',
)
CORS_ALLOW_HEADERS = default_headers + (
    'x-date',
    'X-Api-Key',
    'X-Nonce',
    'Authorization',
    'date',
)

APP_API_KEY = {
    'ios': local_settings.APP_API_KEY_IOS,
    'android': local_settings.APP_API_KEY_ANDROID,
    'HTML5': local_settings.APP_API_KEY_HTML5,
    # 'MINIPROGRAM': local_settings.APP_API_KEY_MINIPROGRAM,
}

ROLEPERMISSIONS_MODULE = 'api.roles'
AUTH_USER_MODEL = "wc_auth.Admin"

FIXTURE_DIRS = (
    BASE_DIR + '/wc_auth/fixtures/',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache'),
        'TIMEOUT': None,
    },

    'memcached': local_settings.CACHES_MEMCACHED,

    'redis': local_settings.CACHES_REDIS,
}

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

MEDIA_ROOT = os.path.join(BASE_DIR, "uploads/")
MEDIA_URL = "/uploads/"

FILE_UPLOAD_PERMISSIONS = 0o0664

STATIC_URL = '/static/'
STATIC_ROOT = ''
STATICFILES_DIRS = ['static']

MEDIA_DOMAIN_HOST = local_settings.MEDIA_DOMAIN_HOST
STATIC_DOMAIN_HOST = local_settings.STATIC_DOMAIN_HOST
SUPER_GAME_SUBDOMAIN = local_settings.SUPER_GAME_SUBDOMAIN_NAME

SMS_APP_KEY = local_settings.SMS_APP_KEY
SMS_APP_SECRET = local_settings.SMS_APP_SECRET
SMS_TYPE = local_settings.SMS_TYPE
SMS_SIGN_NAME = local_settings.SMS_SIGN_NAME
SMS_TEMPLATE_ID = local_settings.SMS_TEMPLATE_ID
SMS_PERIOD_TIME = 60  # 短信间隔时间（秒）
SMS_CODE_EXPIRE_TIME = 60  # 短信验证码有效时间（秒），0表示长期有效,测试期间写长点

WEBSOCKE_SECRET = local_settings.WEBSOCKE_SECRET
ASGI_APPLICATION = 'api.routing.application'
CHANNEL_LAYERS = local_settings.CHANNEL_LAYERS

SMS_CL_SIGN_NAME = local_settings.SMS_CL_SIGN_NAME
SMS_CL_TEMPLATE_REGISTER = local_settings.SMS_CL_TEMPLATE_REGISTER
SMS_CL_TEMPLATE_RESET_PASSWORD = local_settings.SMS_CL_TEMPLATE_RESET_PASSWORD
SMS_CL_TEMPLATE_PASSWORD = local_settings.SMS_CL_TEMPLATE_PASSWORD
SMS_CL_CHANGE_PASSWORD = local_settings.SMS_CL_CHANGE_PASSWORD
SMS_CL_TEMPLATE_SET_PASSCODE = local_settings.SMS_CL_TEMPLATE_SET_PASSCODE
SMS_CL_BINDING_CELL_PHONE = local_settings.SMS_CL_BINDING_CELL_PHONE
SMS_CL_RELIEVE_BINDING_CELL_PHONE = local_settings.SMS_CL_RELIEVE_BINDING_CELL_PHONE

SMS_CL_SIGN_NAME_EN = local_settings.SMS_CL_SIGN_NAME_EN
SMS_CL_TEMPLATE_REGISTER_EN = local_settings.SMS_CL_TEMPLATE_REGISTER_EN
SMS_CL_TEMPLATE_RESET_PASSWORD_EN = local_settings.SMS_CL_TEMPLATE_RESET_PASSWORD_EN
SMS_CL_TEMPLATE_PASSWORD_EN = local_settings.SMS_CL_TEMPLATE_PASSWORD_EN
SMS_CL_CHANGE_PASSWORD_EN = local_settings.SMS_CL_CHANGE_PASSWORD_EN
SMS_CL_TEMPLATE_SET_PASSCODE_EN = local_settings.SMS_CL_TEMPLATE_SET_PASSCODE_EN
SMS_CL_BINDING_CELL_PHONE_EN = local_settings.SMS_CL_BINDING_CELL_PHONE_EN
SMS_CL_RELIEVE_BINDING_CELL_PHONE_EN = local_settings.SMS_CL_RELIEVE_BINDING_CELL_PHONE_EN

BTC_WALLET_API_GUID = local_settings.BTC_WALLET_API_GUID
BTC_WALLET_API_URL = local_settings.BTC_WALLET_API_URL
BTC_WALLET_MAIN_PASSWORD = local_settings.BTC_WALLET_MAIN_PASSWORD

ETH_CONFIRMATIONS = 12

GOOGLE_RECAPTCHA_OPEN = local_settings.GOOGLE_RECAPTCHA_OPEN
CAPTCHA_HTTP_PREFIX = local_settings.CAPTCHA_HTTP_PREFIX
CAPTCHA_GENERATOR = local_settings.CAPTCHA_GENERATOR
CAPTCHA_MATH_CHALLENGE_OPERATOR = '×'

ASIA_GAME_OPEN = local_settings.ASIA_GAME_OPEN

ETHERSCAN_API_URL = local_settings.ETHERSCAN_API_URL
ETHERSCAN_API_KEY = local_settings.ETHERSCAN_API_KEY

DIVIDEND_DECIMAL = local_settings.DIVIDEND_DECIMAL
GSG_TOTAL_SUPPLY = local_settings.GSG_TOTAL_SUPPLY
GSG_LEAST_LOCK_AMOUNT = local_settings.GSG_LEAST_LOCK_AMOUNT
GSG_UNLOCK_PREACT_TIME = local_settings.GSG_UNLOCK_PREACT_TIME

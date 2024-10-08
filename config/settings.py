import os
import ssl

import dj_database_url
import rollbar

from environs import Env


env = Env()
env.read_env()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = env.str('SECRET_KEY', 'django-unsecure')

DEBUG = env.bool('DEBUG', False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', ['127.0.0.1', 'localhost'])
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    ['http://localhost:1337', ]
)

TG_BOT_TOKEN = env.str('TG_BOT_TOKEN', '')
TG_BOT_ADMIN = env.int('TG_BOT_ADMIN')
TG_API_ID = env.int('TG_API_ID')
TG_API_HASH = env.str('TG_API_HASH', '')
TG_SESSION = env.str('TG_SESSION', '')
TG_GET_MESSAGE_FROM = env.int('TG_GET_MESSAGE_FROM')
TG_ADDITIONAL_CHAT_ID = env.int('TG_ADDITIONAL_CHAT_ID')

XML_LOGIN = env.str('XML_LOGIN')
XML_PASSWORD = env.str('XML_PASSWORD')

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.set_ciphers('DEFAULT')
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

MAIL_LOGIN = env.str('MAIL_LOGIN', '')
MAIL_PASSWORD = env.str('MAIL_PASSWORD', '')
MAIL_IMAP_SERVER = env.str('MAIL_IMAP_SERVER', '')

SIMPLEONE_API = env.str('SIMPLEONE_API', '')
SIMPLEONE_USER = env.str('SIMPLEONE_USER', '')
SIMPLEONE_PASSWORD = env.str('SIMPLEONE_PASSWORD', '')

TASK_ESCALATION = env.int('TASK_ESCALATION', 10)
TASK_DEADLINE = env.int('TASK_DEADLINE', 120)

SYNC_TIMEOUT = env.int('SYNC_TIMEOUT', 7)

REDIS_HOST = env.str('REDIS_HOST', '')
REDIS_PORT = env.int('REDIS_PORT', 6379)

ROLLBAR_ACCESS_TOKEN = env.str('ROLLBAR_ACCESS_TOKEN', '')
ROLLBAR_ENV = env.str('ROLLBAR_ENV', 'dev')
ROLLBAR = {
    'access_token': ROLLBAR_ACCESS_TOKEN,
    'environment': ROLLBAR_ENV,
    'root': BASE_DIR,
}
rollbar.init(ROLLBAR_ACCESS_TOKEN, ROLLBAR_ENV)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'src',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'rollbar.contrib.django.middleware.RollbarNotifierMiddlewareExcluding404',
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

DATABASES = {
    'default': dj_database_url.config(
        default=env.str('DB_URL', 'sqlite:///db.sqlite3'),
    )
}

AUTH_USER_MODEL = 'src.CustomUser'
LOGIN_REDIRECT_URL = '/dealers'

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

STATIC_URL = env.str('STATIC_URL', '/static/')
STATIC_ROOT = env.str('STATIC_ROOT', os.path.join(BASE_DIR, 'static'))

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

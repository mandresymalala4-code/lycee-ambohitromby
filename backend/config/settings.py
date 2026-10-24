import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-insecure-key-change-me')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
if not DEBUG and SECRET_KEY.startswith(('dev-insecure', 'lycee-ambohitromby-cle-secrete')):
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Production (DEBUG=False) : définissez une SECRET_KEY unique et secrète dans le fichier .env.")
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')] + ['testserver']

INSTALLED_APPS = [
    'django.contrib.contenttypes', 'django.contrib.auth',
    'corsheaders', 'rest_framework', 'rest_framework_simplejwt.token_blacklist',
    'comptes', 'scolarite', 'notes', 'absences', 'documents',
]
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'comptes.middleware.NoCacheMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = []
WSGI_APPLICATION = 'config.wsgi.application'
AUTH_USER_MODEL = 'comptes.Utilisateur'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if os.getenv('DB_ENGINE', 'mysql') == 'sqlite':
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
else:
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'lycee_ambohitromby'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {'charset': 'utf8mb4', 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"},
        'TEST': {'CHARSET': 'utf8mb4', 'COLLATION': 'utf8mb4_unicode_ci'},
    }}

# Compatibilité XAMPP : il fournit MariaDB 10.4, alors que Django 5.2 en annonce 10.5 minimum.
# Les fonctions utilisées par l'application fonctionnent sur MariaDB 10.4 : on lève seulement ce blocage.
if os.getenv('DB_ENGINE', 'mysql') != 'sqlite':
    from django.db.backends.mysql.base import DatabaseWrapper as _MyWrapper
    from django.db.utils import NotSupportedError as _NSE
    _orig_check = _MyWrapper.check_database_version_supported

    def _check_version(self):
        try:
            _orig_check(self)
        except _NSE as e:  # MariaDB 10.4.x uniquement
            if 'MariaDB 10.5' not in str(e) or not str(self.mysql_server_info).startswith('10.4'):
                raise

    _MyWrapper.check_database_version_supported = _check_version

PASSWORD_HASHERS = ['django.contrib.auth.hashers.PBKDF2PasswordHasher']
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Indian/Antananarivo'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DATA_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024 * 1024

CORS_ALLOWED_ORIGINS = [o.strip().rstrip('/') for o in os.getenv('CORS_ORIGIN', 'http://localhost:5173').split(',') if o.strip()]
CORS_ALLOW_HEADERS = ['authorization', 'content-type', 'accept', 'origin']

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['comptes.auth.StatutJWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'EXCEPTION_HANDLER': 'comptes.errors.exception_handler',
    'UNAUTHENTICATED_USER': None,
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=8),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'UPDATE_LAST_LOGIN': False,
    'BLACKLIST_AFTER_ROTATION': False,
}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
LOGGING = {'version': 1, 'disable_existing_loggers': False,
           'handlers': {'console': {'class': 'logging.StreamHandler'}},
           'loggers': {'lycee': {'handlers': ['console'], 'level': 'ERROR'}}}

# Constantes métier (§15)
ELEVE_NAISSANCE_MIN = '1998-01-01'
ELEVE_NAISSANCE_MAX = '2013-12-31'
SEUIL_ALERTE_ABSENCES = 15

# Production (hébergement derrière un proxy HTTPS : PythonAnywhere, etc.)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_REFERRER_POLICY = 'same-origin'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

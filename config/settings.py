# config/settings.py
from pathlib import Path
import os
import importlib
import importlib.util

from django.core.exceptions import ImproperlyConfigured
from urllib.parse import urlsplit

# ========================================
# BASE DIR / ENV
# ========================================
BASE_DIR = Path(__file__).resolve().parent.parent

# .env opcional (não falha se faltar)
if importlib.util.find_spec("dotenv"):
    dotenv = importlib.import_module("dotenv")
    dotenv.load_dotenv(BASE_DIR / ".env")

# ========================================
# SEGURANÇA BÁSICA
# ========================================
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ("1", "true", "on")

if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY não definido nas variáveis de ambiente.")

# Hosts/Origens
def _normalize_allowed_host(raw_host: str) -> str:
    host = raw_host.strip()
    if not host:
        return ""
    if "://" in host:
        return urlsplit(host).hostname or ""
    host = host.split("/")[0]
    if host.startswith("[") and "]" in host:
        return host[: host.index("]") + 1]
    if ":" in host:
        host = host.split(":")[0]
    return host


_default_allowed_hosts = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "foodlens.com.br",
    "www.foodlens.com.br",
    "177.153.58.19",
]

_allowed_hosts_raw = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
_env_allowed_hosts = [
    host
    for host in (
        _normalize_allowed_host(h)
        for h in _allowed_hosts_raw.split(",")
    )
    if host
]

if DEBUG:
    _candidate_allowed_hosts = [*_env_allowed_hosts, *_default_allowed_hosts]
else:
    _candidate_allowed_hosts = _env_allowed_hosts or _default_allowed_hosts

ALLOWED_HOSTS = [
    *[
        host
        for host in dict.fromkeys(_candidate_allowed_hosts)
        if host
    ]
]

# CSRF confiável (importante para POST via navegador quando usar IP/host público)
CSRF_TRUSTED_ORIGINS = [
    *(f"http://{h}" for h in ALLOWED_HOSTS if h not in ("localhost", "127.0.0.1")),
    *(f"https://{h}" for h in ALLOWED_HOSTS if h not in ("localhost", "127.0.0.1")),
]

# ========================================
# DEPENDÊNCIAS OPCIONAIS (imports seguros)
# ========================================
_has_cors = False
if importlib.util.find_spec("corsheaders"):
    _cors_default_headers = importlib.import_module(
        "corsheaders.defaults"
    ).default_headers
    _has_cors = True
else:
    # corsheaders não instalado — seguimos sem CORS
    _cors_default_headers = tuple()

# ========================================
# APPS
# (ordem importa: 'sites' antes do allauth; apps Django primeiro)
# ========================================
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",        # necessário para allauth
    "django.contrib.gis",          # PostGIS/GIS

    # Terceiros
    "leaflet",                     # django-leaflet
    "rest_framework",              # djangorestframework (se não usar, remova)
    "rest_framework.authtoken",
    "allauth",                     # django-allauth
    "allauth.account",
    "allauth.socialaccount",
    # "allauth.socialaccount.providers.google",  # habilite se for usar Google OAuth
    *(["corsheaders"] if _has_cors else []),    # só adiciona se instalado

    # Suas apps
    "mapping",
]

SITE_ID = int(os.environ.get("DJANGO_SITE_ID", "1"))

# ========================================
# MIDDLEWARE
# (corsheaders deve vir antes de CommonMiddleware)
# ========================================
MIDDLEWARE = [
    *(["corsheaders.middleware.CorsMiddleware"] if _has_cors else []),
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # allauth
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ========================================
# URLS / TEMPLATES / WSGI
# ========================================
ROOT_URLCONF = "config.urls"

TEMPLATE_DIR = BASE_DIR / "templates"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATE_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # requerido pelo allauth
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # ATENÇÃO: se você NÃO tiver esse processor, comente a linha abaixo:
                "config.context_processors.revisor_status",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ========================================
# DATABASE (POSTGIS)
# ========================================
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("POSTGRES_DB", "pancdb"),
        "USER": os.environ.get("POSTGRES_USER", "pancuser"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,  # mantém conexões por 1 min
    }
}

# ========================================
# STATIC / MEDIA
# ========================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "mapping" / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ========================================
# AUTENTICAÇÃO / ALLAUTH
# ========================================
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Configurações do allauth (versão 65.x)
ACCOUNT_EMAIL_VERIFICATION = os.environ.get("DJANGO_EMAIL_VERIFICATION", "optional")
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]

# ========================================
# E-MAIL
# ========================================
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_DEFAULT_FROM_EMAIL", "no-reply@colaborapanc.com")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() in ("1", "true", "on")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

# ========================================
# INTERNACIONALIZAÇÃO
# ========================================
LANGUAGE_CODE = "pt-br"
LANGUAGES = [
    ("pt-br", "Português (Brasil)"),
    ("en", "English"),
    ("es", "Español"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# ========================================
# DRF (básico, remova se não usar)
# ========================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

# ========================================
# CORS (apenas se corsheaders instalado)
# ========================================
if _has_cors:
    # Em produção, SEMPRE use whitelist específica (mais seguro)
    CORS_ALLOW_ALL_ORIGINS = DEBUG and os.environ.get("CORS_ALLOW_ALL_ORIGINS", "False").lower() in ("1", "true", "on")
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_HEADERS = list(_cors_default_headers) + ["X-CSRFToken"]

    # Whitelist de origens permitidas (usar em produção)
    if not CORS_ALLOW_ALL_ORIGINS:
        CORS_ALLOWED_ORIGINS = [
            *[o.strip() for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
        ]

# ========================================
# LEAFLET
# ========================================
LEAFLET_CONFIG = {
    "DEFAULT_CENTER": (-14.2, -51.9),
    "DEFAULT_ZOOM": 4,
    "MIN_ZOOM": 2,
    "MAX_ZOOM": 18,
    "SCALE": "both",
    "ATTRIBUTION_PREFIX": "ColaboraPANC",
    "TILES": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    "ATTRIBUTION": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}

# ========================================
# MONITORAMENTO AMBIENTAL (MapBiomas/FIRMS)
# ========================================
MAPBIOMAS_EMAIL = os.environ.get("MAPBIOMAS_EMAIL", "warleyalisson@gmail.com")
MAPBIOMAS_PASSWORD = os.environ.get("MAPBIOMAS_PASSWORD", "W9j3pp.@")
MAPBIOMAS_API_URL = os.environ.get(
    "MAPBIOMAS_API_URL",
    "https://plataforma.alerta.mapbiomas.org/api/v2/graphql",
)

NASA_FIRMS_MAP_KEY = os.environ.get("NASA_FIRMS_MAP_KEY", "7fbc21c81aae4bc959d830a9250be833")
NASA_FIRMS_SOURCE = os.environ.get("NASA_FIRMS_SOURCE", "VIIRS_SNPP_NRT")
NASA_FIRMS_API_URL = os.environ.get(
    "NASA_FIRMS_API_URL",
    "https://firms.modaps.eosdis.nasa.gov/api/area/csv",
)

ALERT_MONITOR_RADIUS_METERS = int(os.environ.get("ALERT_MONITOR_RADIUS_METERS", "5000"))
ALERT_MONITOR_DEFAULT_DAYS = int(os.environ.get("ALERT_MONITOR_DEFAULT_DAYS", "7"))
ALERT_MONITOR_TIMEOUT_SECONDS = int(os.environ.get("ALERT_MONITOR_TIMEOUT_SECONDS", "20"))

# ========================================
# INTEGRAÇÕES EXTERNAS (CHAVES TEMPORÁRIAS DE TESTE)
# ========================================
GNAMES_API_URL = os.environ.get("GNAMES_API_URL", "https://verifier.globalnames.org/api/v1")
TROPICOS_API_URL = os.environ.get("TROPICOS_API_URL", "https://services.tropicos.org")
TROPICOS_API_KEY = os.environ.get("TROPICOS_API_KEY", "dc34a4c3-1bf2-4edf-9488-b11e9f860744")
GBIF_API_URL = os.environ.get("GBIF_API_URL", "https://api.gbif.org/v1")
INAT_API_URL = os.environ.get("INAT_API_URL", "https://api.inaturalist.org/v1")
TREFLE_API_URL = os.environ.get("TREFLE_API_URL", "https://trefle.io/api/v1")
TREFLE_API_TOKEN = os.environ.get("TREFLE_API_TOKEN", "usr-V8E4TFez3OflTjXOHHV3hltc2J4231KmVysctucAGD4")
TREFLE_TOKEN = os.environ.get("TREFLE_TOKEN", TREFLE_API_TOKEN)
PLANTID_API_KEY = os.environ.get("PLANTID_API_KEY", "eMdpEzAOCDtfNRT1gfZrsvFBJzOnFmaFy5diWCdM1hYBOXOg7A")

# Espelha defaults no ambiente para compatibilidade com serviços que leem via os.environ.
os.environ.setdefault("GNAMES_API_URL", GNAMES_API_URL)
os.environ.setdefault("TROPICOS_API_URL", TROPICOS_API_URL)
os.environ.setdefault("TROPICOS_API_KEY", TROPICOS_API_KEY)
os.environ.setdefault("GBIF_API_URL", GBIF_API_URL)
os.environ.setdefault("INAT_API_URL", INAT_API_URL)
os.environ.setdefault("TREFLE_API_URL", TREFLE_API_URL)
os.environ.setdefault("TREFLE_API_TOKEN", TREFLE_API_TOKEN)
os.environ.setdefault("TREFLE_TOKEN", TREFLE_TOKEN)
os.environ.setdefault("PLANTID_API_KEY", PLANTID_API_KEY)
os.environ.setdefault("MAPBIOMAS_EMAIL", MAPBIOMAS_EMAIL)
os.environ.setdefault("MAPBIOMAS_PASSWORD", MAPBIOMAS_PASSWORD)
os.environ.setdefault("NASA_FIRMS_MAP_KEY", NASA_FIRMS_MAP_KEY)

# ========================================
# WIKIMEDIA / WIKIPEDIA (ENRIQUECIMENTO CONTROLADO)
# ========================================
COLABORAPANC_VERSION = os.environ.get("COLABORAPANC_VERSION", "1.0")
WIKIMEDIA_USER = os.environ.get("WIKIMEDIA_USER", "Warleyalisson")
WIKIMEDIA_EMAIL = os.environ.get("WIKIMEDIA_EMAIL", "warleyalisson@gmail.com")
_default_wikimedia_agent = f"ColaboraPANC/{COLABORAPANC_VERSION} ({WIKIMEDIA_USER}; {WIKIMEDIA_EMAIL})"
WIKIMEDIA_USER_AGENT = os.environ.get("WIKIMEDIA_USER_AGENT", _default_wikimedia_agent)
WIKIMEDIA_API_USER_AGENT = os.environ.get("WIKIMEDIA_API_USER_AGENT", WIKIMEDIA_USER_AGENT)
WIKIMEDIA_ENRICHMENT_ENABLED = os.environ.get("WIKIMEDIA_ENRICHMENT_ENABLED", "True").lower() in ("1", "true", "on")
WIKIMEDIA_TIMEOUT_SECONDS = float(os.environ.get("WIKIMEDIA_TIMEOUT_SECONDS", "8"))
WIKIMEDIA_HTTP_RETRIES = int(os.environ.get("WIKIMEDIA_HTTP_RETRIES", "2"))
WIKIMEDIA_MIN_MATCH_CONFIDENCE = float(os.environ.get("WIKIMEDIA_MIN_MATCH_CONFIDENCE", "0.55"))

# ========================================
# SENHAS / VALIDADORES
# ========================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ========================================
# LOGGING
# ========================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOG_DIR = BASE_DIR / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] [{levelname}] {name} {message}", "style": "{"},
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "config.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "verbose",
        },
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "loggers": {
        "django": {"handlers": ["file", "console"], "level": "INFO", "propagate": True},
        "mapping": {"handlers": ["file", "console"], "level": "INFO", "propagate": True},
    },
}

# ========================================
# SEGURANÇA EXTRA (produção)
# ========================================
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 3600 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_REFERRER_POLICY = os.environ.get(
    "DJANGO_SECURE_REFERRER_POLICY",
    "strict-origin-when-cross-origin",
)
X_FRAME_OPTIONS = "DENY"

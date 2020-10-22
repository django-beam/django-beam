DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

INSTALLED_APPS = [
    "beam",
    "beam.themes.bootstrap4",
    "testapp",
    "crispy_forms",
    "django.contrib.contenttypes",
    # "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.auth",
    # contrib.reversion
    "reversion",
    "beam.contrib.reversion",
    # contrib.autocomplete_light
    "dal",
    "beam.contrib.autocomplete_light",
    "dal_select2",
]

SECRET_KEY = "secret_key_for_testing"

ROOT_URLCONF = "testapp.urls"

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

STATIC_URL = "/static/"

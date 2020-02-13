import django


def pytest_configure(config):
    from django.conf import settings

    settings.configure(
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        },
        INSTALLED_APPS=[
            "beam",
            "beam.themes.bootstrap4",
            "testapp",
            "crispy_forms",
            "django.contrib.contenttypes",
            "django.contrib.admin",
            "django.contrib.auth",
            "reversion",
            "beam.contrib.reversion",
        ],
        SECRET_KEY="secret_key_for_testing",
        ROOT_URLCONF="testapp.urls",
        TEMPLATES=[
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
        ],
    )
    django.setup()

import django


def pytest_configure(config):
    from django.conf import settings

    settings.configure(
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        },
        INSTALLED_APPS=["beam", "beam.themes.bootstrap4", "testapp", "crispy_forms"],
        SECRET_KEY="secret_key_for_testing",
        ROOT_URLCONF="testapp.urls",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "APP_DIRS": True,
                "OPTIONS": {},
            }
        ],
    )
    django.setup()

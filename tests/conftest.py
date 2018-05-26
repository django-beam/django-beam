import django


def pytest_configure(config):
    from django.conf import settings

    settings.configure(
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        },
        INSTALLED_APPS=["beam", "testapp"],
        SECRET_KEY="secret_key_for_testing",
    )
    django.setup()

import django
import pytest
from django.conf import settings
from django.core.management import call_command


def pytest_configure():
    settings.configure(
        SECRET_KEY="secret",
        INSTALLED_APPS=[
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "django.contrib.gis",
            "testapp",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.contrib.gis.db.backends.spatialite",
                "NAME": "db.sqlite",
                "TEST": {
                    "NAME": ":memory:",
                },
            }
        },
        LANGUAGE_CODE="en-us",
        TIME_ZONE="UTC",
        USE_I18N=True,
        USE_TZ=True,
    )
    django.setup()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", "test.json")

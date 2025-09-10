============
beam.contrib
============

We include a ``beam.contrib`` package that provides integration with several third party django apps.

beam.contrib.auth
-----------------

Provides viewsets for editing users and groups as well as (optional) templates for use with the
default django registration views.

Usage
^^^^^

If you just want the ability to edit users and groups, add the following to a ``urls.py`` in your
project.

.. code-block:: python

    urlpatterns = [
        path("auth/", include("beam.contrib.auth.urls")),
        ...
    ]

If you want to make use of the default templates for login, logout and password reset you'll need to
do a bit more.

Add ``beam.contrib.auth`` to your installed apps **before** ``django.contrib.admin`` so the templates
will be picked up.


.. code-block:: python

    # In your settings.py:
    INSTALLED_APPS = [
        "beam.contrib.auth",
        "django.contrib.admin",
        "django.contrib.auth",
        # ...
    ]

    # redirect to something other than the default /accounts/profile/
    LOGIN_REDIRECT_URL = "/"


    # In your urls.py:
    urlpatterns = [
       path("auth/", include("beam.contrib.auth.urls")),
       path("accounts/", include("django.contrib.auth.urls")),
       path("accounts/", include("beam.contrib.auth.urls")),
       # ...
    ]

Now you should be able to use e.g. ``/accounts/login/`` to login, reset your password via the forgot
password link and so on.


beam.contrib.autocomplete_light
-------------------------------

Provides a viewset mixin for integration with ``django-autocomplete-light``.
It also provides some bootstrap compatible css to override django-autocomplete-light defaults. To use those
you'll have to add ``beam.contrib.autocomplete_light`` to your installed apps *before* ``django-autocomplete-light``.

Usage
^^^^^

Add the mixin to your viewset, then use ``django-autocomplete-light`` as per the projects docs, for
example by overriding the widget dicts.

.. code-block:: python

    # settings.py
    INSTALLED_APPS = [
        "beam.contrib.autocomplete_light",
        "dal",
        "dal_select2",
        ...
    ]

    # views.py
    import beam
    from .models import Book, Author
    from .forms import BookForm
    from beam.contrib.autocomplete_light import AutocompleteMixin

    class BookViewSet(beam.ViewSet):
        model = Book
        fields = ["title", "author"]
        form_class = BookForm

    class AuthorViewSet(AutocompleteMixin, beam.ViewSet):
        model = Author
        fields = ["title"]
        autocomplete_search_fields = ["title"]

    # forms.py
    from django import forms
    from .models import Book
    from dal_select2.widgets import ModelSelect2

    class BookForm(forms.ModelForm):
        class Meta:
            model = Book
            fields = ["title", "author"]
            widgets = {
                "author": ModelSelect2(
                    url="PROJECTNAME/APP_LABEL/author_autocomplete",
                ),
            }


beam.contrib.reversion
----------------------

This is somewhat experimental and should be considered alpha quality.
Provides a base viewset for integration with ``django-reversion``.

Usage
^^^^^

First add ``reversion`` and ``beam.contrib.reversion`` to your installed apps.
Either use ``beam.contrib.reversion.VersionViewSet`` as the base class for the
models where you want reversion or use the ``VersionViewSetMixin``.

By default create and update views are tracked. You can use the ``versioned_facet_names``
class attribute to control which facets are tracked.

If you do not manually register your models with reversion then ``VersionViewSet.model`` is registered
following all the inlines specified for the ``versioned_facet_names``.

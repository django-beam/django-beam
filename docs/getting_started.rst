===============
Getting started
===============

Installation
------------
Install django-beam using pip:

.. code-block:: bash

    pip install django-beam


Add ``beam``, ``beam.themes.boostrap4`` and ``crispy_forms`` to your ``INSTALLED_APPS`` in `settings.py`:


.. code-block:: python

    # in your settings.py
    INSTALLED_APPS = [
        # ...
        "beam",
        "beam.themes.bootstrap4",
        "crispy_forms",
    ]



Quickstart example
------------------
Let's say you have a list of books that you want to manage in your Django project. You can use django-beam to quickly create a list view, detail view, create view and update view for your books.
Note that your test app must not have an ``app_name`` in `urls.py`.

.. code-block:: python

    # books/models.py
    from django.db import models

    class Book(models.Model):
        title = models.CharField(max_length=255)
        author = models.ForeignKey("Author", on_delete=models.CASCADE, related_name="books")


    class Author(models.Model):
        title = models.CharField(max_length=255)

    # books/views.py
    import beam

    class BookViewSet(beam.ViewSet):
        model = Book
        fields = ['title', 'author']

    class AuthorViewSet(beam.ViewSet):
        model = Author
        fields = ['name']

    # books/urls.py
    from django.urls import path, include

    # app_name = ... must not be set in this file
    urlpatterns = [
        path('books/', include(BookViewSet().get_urls())),
        path('authors/', include(AuthorViewSet().get_urls())),
        # ...
    ]

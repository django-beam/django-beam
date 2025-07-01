# django-beam [![CI](https://github.com/django-beam/django-beam/actions/workflows/tox.yml/badge.svg)](https://github.com/django-beam/django-beam/actions/workflows/tox.yml) [![ReadTheDocs](https://readthedocs.org/projects/django-beam/badge/)](https://django-beam.readthedocs.io/en/latest/) [![codecov](https://codecov.io/gh/django-beam/django-beam/branch/master/graph/badge.svg?token=U0C27SY9XM)](https://codecov.io/gh/django-beam/django-beam)

django-beam provides you with a set of views, templates, and integrations for the most common CRUD applications. It aims to offer the functionality of Django's own admin but in a way that integrates seamlessly with your frontend code.

## Breaking changes

In version 3.0 `Component` was renamed to `Facet` in order to reduce confusion with web components.

## Features

- CRUD operations based on class-based views
- Easily extensible
- Extensions for common use cases and popular third-party packages

## Documentation

The full documentation can be found at [https://django-beam.readthedocs.io/en/latest/](https://django-beam.readthedocs.io/en/latest/).

## Quickstart

To get started, you'll need to follow these steps:

1. Install django-beam:

```bash
pip install django-beam
```

2. Add "beam" and "crispy_forms" to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    "beam",
    "beam.themes.bootstrap4",
    "crispy_forms",
]
```

3. Import and use `beam` in your Django project, as shown in the example below:

```python
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
    fields = ['title']

# urls.py
from django.urls import path, include

urlpatterns = [
    path('books/', include(BookViewSet().get_urls())),
    path('authors/', include(AuthorViewSet().get_urls())),
    # ...
]
```

For more examples and detailed explanations of various django-beam features, refer to the [full documentation](https://django-beam.readthedocs.io/en/latest/).

## beam.contrib

The `beam.contrib` package provides integration with several third-party Django apps, such as:

- `beam.contrib.auth`: Viewsets for editing users and groups, and optional templates for default Django registration views.
- `beam.contrib.autocomplete_light`: Integration with `django-autocomplete-light`.
- `beam.contrib.reversion`: Experimental integration with `django-reversion`.

Refer to the documentation for usage instructions on each of the contrib packages.

## Testing

You can use the [tox](https://tox.readthedocs.io/en/latest/) testing tool to run the tests:

```bash
tox -e py312-django_latest
```

Run the tests of a specific test file only:

```bash
tox -e py312-django_latest -- test_tags
```

Run against all supported versions of Python and Django:

```bash
tox
```

## Support

If you encounter any issues or have questions, please refer to the [django-beam documentation](https://django-beam.readthedocs.io/en/latest/) or raise an issue on the [GitHub repository](https://github.com/yourgithubuser/django-beam/issues).

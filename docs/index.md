# django-beam

django-beam provides you with a set of views, templates and integrations for the most common CRUD
applications. 

The goal is having the functionality provided by django's own admin, but in a way that integrates
with your other frontend code. 


## Requirements
* [Python](https://www.python.org/) 3.6+
* [Django](https://www.djangoproject.com/) 2.0+


## Installation
Installing from pypi.
```bash
pip install django-beam
```

Installing from [GitHub](https://github.com/django-beam/django-beam).
```bash
pip install -e git+https://github.com/django-beam/django-beam.git#egg=django-beam
```


## Getting started
Add `django-beam` to you `INSTALLED_APPS` and select a theme you like.
```python
# settings.py
INSTALLED_APPS += [
    "beam",
    "beam.themes.bootstrap4",  # or choose any theme you like
]
```

## Example
[Example](example.md#example)

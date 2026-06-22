=============
Release notes
=============

4.0.0
=====

Breaking changes
----------------

- django-beam now depends on ``django-crispy-forms`` 2.x.

Migration
---------

Upgrade django-beam and update your Django settings:

.. code-block:: bash

    pip install --upgrade django-beam

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "beam",
        "beam.themes.bootstrap4",
        "crispy_bootstrap4",
        "crispy_forms",
    ]

    CRISPY_ALLOWED_TEMPLATE_PACKS = ("bootstrap4",)
    CRISPY_TEMPLATE_PACK = "bootstrap4"

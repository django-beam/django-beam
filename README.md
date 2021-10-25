[![CircleCI](https://circleci.com/gh/django-beam/django-beam.svg?style=svg)](https://circleci.com/gh/django-beam/django-beam)
[![ReadTheDocs](https://readthedocs.org/projects/django-beam/badge/)](https://django-beam.readthedocs.io/en/latest/)
[![codecov](https://codecov.io/gh/django-beam/django-beam/branch/master/graph/badge.svg?token=U0C27SY9XM)](https://codecov.io/gh/django-beam/django-beam)

# django-beam

django-beam provides you with a set of views, templates and integrations for the most common CRUD
applications.

The goal is having the functionality provided by django's own admin, but in a way that integrates with your other frontend code.

## This project is still in early development.

Most of the core concepts have stabilized and it is being used in production. However there may
still be breaking changes going forward

## Features

- CRUD operations based on class based views
- Easily extensible
- Extensions for common use cases and popular third party packages

## Documentation

Should end up at https://django-beam.readthedocs.io/en/latest/

## Example

```
    # people/models.py
    class Group(models.Model):
        name = models.TextField()


    class Person(models.Model):
        name = models.TextField()
        email = models.EmailField()

        groups = models.ManyToManyField(Group)


    # people/views.py
    import beam

    class PersonViewSet(beam.ViewSet):
        model = Person
        fields = ['name', 'groups']


    class GroupViewSet(beam.ViewSet):
        model = Group
        fields = ['name']


    # urls.py
    urlpatterns += [
        path('person/', include(PersonViewSet().get_urls())),
        path('group/', include(GroupViewSet().get_urls())),
    ]


    # settings.py
    INSTALLED_APPS += [
        "beam",
        "beam.themes.bootstrap4",  # or choose any theme you like
        "crispy_forms",  # required by the bootstrap4 theme
    ]
```

## Core concepts

There are a few pieces beyond standard django that you need to understand to use beam.
The first one are **ViewSets**. They are used to group and configure several views for a single model (similar to
`django-rest-framework`). Specifying e.g. `fields = ["name", "age"]` will pass those fields to all views for the specified model. They also allow you to specify and override configuration for single views, by setting e.g. `update_fields = ["name"]` the update view will be restricted to just the name.

The next concept are **Components**. Components are used to group and pass relevant attributes from
the viewset to the individual views. A view is only passed data that it's component expects in
`__init__`.

The viewset figures out which attributes should be passed to a component and also takes into account
the specificity. If you specify both `fields` and `detail_fields`, the detail component will receive
the latter, while all other components will be passed the former.

### Example of using a custom component

Below you can see an example of adding a custom view

```
class CustomerCallView(beam.views.ComponentMixin, MyBaseView):
    phone = None
    # your custom view code goes here ...

class CustomerViewSet(beam.ViewSet):
    model = Customer
    fields = ["first_name", "last_name", "email", "phone"]

    call_component = Component
    call_url = "call/{phone}/"
    call_url_kwargs = {"phone": "phone"}
    call_permission = "customers.view_customer"
```

## Layouts

### Form layouts

Beam layouts are a simple way to give forms and detail views
some structure without the use of custom templates.
By specifying a tripple nested list on the viewset, fields can be grouped into
rows and columns. The default theme supports up to 4 columns per row.

```
layout = [
    [ # first row
        ["name", "age",],   # first column
        ["phone", "email",],   # second column
    ]
    [ # second row
        ["a", "b",],   # first column
        ["c", "d",],   # second column
    ]
]
```

FIXME IMAGE

### Link layouts

Beam shows links to other views in the viewset both at the top of all pages
as well as next to items in the list page.
In order to specify which links should be visible at the top of the detail page,
you can e.g. specify `detail_links = ["update", "...", "delete", "!create"]`.
This would cause create to be hidden, the first link to be to the update view, the last one to
the delete view and all other components would show up in between those two.

If you e.g. want the create view to be the only one shown at the top of the list view, set
`list_links = ["create"]`. To specify the links shown next to list items, set `list_item_links`.

## Inlines

```
class ContactDataInline(beam.RelatedInline):
    model = ContactData
    foreign_key_field = 'person'
    fields = ["medium", "value"]


class PersonViewSet(beam.ViewSet):
    model = Person
    create_inline_classes = []
    inline_classes = [ContactDataInline]

```

## Themes

We currently ship only one theme.

- `beam.themes.bootstrap4`
  Using default Bootstrap v4 markup and include a basic Bootstrap CSS file.

  In order to use the bootstrap4 theme you have to install the optional dependency
  `django-crispy-forms` and add it to your `INSTALLED_APPS` in settings.py:

  ```
  INSTALLED_APPS = (..., 'crispy_forms')
  ```

## beam.contrib

We include a `beam.contrib` package that provides integration with several third party django apps.

### beam.contrib.reversion

Provides a base viewset for integration with `django-reversion`.

#### Usage

First add `reversion` and `beam.contrib.reversion` to your installed apps.
Either use `beam.contrib.reversion.VersionViewSet` as the base class for the
models where you want reversion or use the `VersionViewSetMixin`.

By default create and update views are tracked. You can use the `versioned_component_names`
class attribute to control which components are tracked.

If you do not manually register your models with reversion then `VersionViewSet.model` is registered
following all the inlines specified for the `versioned_component_names`.

### beam.contrib.autocomplete_light

Provides a viewset mixin for integration with `django-autocomplete-light`.
It also provides some bootstrap compatible css to override django-autocomplete-light defaults. To use those
you'll have to add `beam.contrib.autocomplete_light` to your installed apps _before_ `django-autocomplete-light`.

#### Usage

Add the mixin to your viewset, then use `django-autocomplete-light` as per the projects docs, for
example by overriding the widget dicts.

```python
# settings.py
INSTALLED_APPS = [
    "beam.contrib.autocomplete_light",
    "dal",
    "dal_select2",
    ...
]

# views.py
import beam
from beam.contrib.autocomplete_light import AutocompleteMixin

class GroupViewSet(AutocompleteMixin, beam.ViewSet):
    fields = ['name']
    autocomplete_search_fields = ["name"]

# forms.py
from django import forms
from people.models import Person

from dal_select2.widgets import ModelSelect2Multiple

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["name", "email", "groups"]
        widgets = {
            "groups": ModelSelect2Multiple(
                url="people_group_autocomplete"
            ),
        }
```

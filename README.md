# django-beam
django-beam provides you with a set of views, templates and integrations for the most common CRUD
applications. 

The goal is having the functionality provided by django's own admin, but in a way that integrates
with your other frontend code. 

## Features
- CRUD operations based on class based views
- Default templates with multiple themes (bootstrap 4, ...)
- Extensions for common use cases, e.g. export as csv, ...
- Support for related models (autocompletion, linking, ...)
- Familiar interfaces

# Example
```
# models.py
class Group(models.Model):
    name = models.TextField()

    
class Person(models.Model):
    name = models.TextField()
    email = models.EmailField()

    groups = models.ManyToManyField(Group)


# views.py
import beam

class PersonViewSet(beam.ViewSet):
    fields = ['name', 'groups']


class GroupViewSet(beam.ViewSet):
    fields = ['name']


# urls.py
urlpatterns += [
    path('person/', include(PersonViewSet().get_urls())),
    path('group/', include(GroupViewSet().get_urls())),
]


# settings.py
INSTALLED_APPS += ['beam']
```

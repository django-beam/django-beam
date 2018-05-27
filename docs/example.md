# Example

```python
# models.py
from django.db import models
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
from django.urls import path, include
urlpatterns += [
    path('person/', include(PersonViewSet().get_urls())),
    path('group/', include(GroupViewSet().get_urls())),
]


# settings.py
INSTALLED_APPS += [
    "beam",
    "beam.themes.bootstrap4",  # or choose any theme you like
]
```

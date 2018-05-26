from django.urls import path, include

from .views import DragonflyViewSet

urlpatterns = [path("dragonfly/", include(DragonflyViewSet().get_urls()))]

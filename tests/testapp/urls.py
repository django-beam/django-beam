from django.urls import include, path

from .views import DragonflyViewSet, SightingViewSet

urlpatterns = [
    path("dragonfly/", include(DragonflyViewSet().get_urls())),
    path("sighting/", include(SightingViewSet().get_urls())),
]

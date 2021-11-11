from django.urls import include, path
from django.views.generic import TemplateView

from .views import DragonflyViewSet, SightingViewSet

urlpatterns = [
    path("dragonfly/", include(DragonflyViewSet().get_urls())),
    path("sighting/", include(SightingViewSet().get_urls())),
    path(
        "base_template/",
        TemplateView.as_view(template_name="beam/base.html"),
        name="base-template",
    ),
]

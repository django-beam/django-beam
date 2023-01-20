from django.urls import include, path

from beam.contrib.auth.views import GroupViewSet, UserViewSet

urlpatterns = [
    path("user/", include(UserViewSet().get_urls())),
    path("group/", include(GroupViewSet().get_urls())),
]

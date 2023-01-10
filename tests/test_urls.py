from unittest import mock

from django.test import TestCase
from django.test.utils import override_settings
from django.urls import NoReverseMatch, include, path, reverse
from testapp.models import Dragonfly
from testapp.views import DragonflyViewSet, SightingViewSet

from beam.templatetags.beam_tags import get_link_url, get_url_for_related

urlpatterns = [
    path(
        "dragonfly/",
        include(
            (DragonflyViewSet().get_urls(), "my_app_name"), namespace="my_namespace"
        ),
    ),
    path(
        "sighting/",
        include(
            (SightingViewSet().get_urls(), "my_app_name"), namespace="my_namespace"
        ),
    ),
]


class UrlTest(TestCase):
    def test_get_urls_produces_urls(self):
        self.assertEqual(len(DragonflyViewSet().get_urls()), 6)

    def test_get_links_contains_all_view_types(self):
        self.assertSetEqual(
            set(DragonflyViewSet().links.keys()),
            {"list", "detail", "update", "create", "delete", "extra"},
        )

    def test_url_patterns_are_correct(self):
        expected = {
            "testapp_dragonfly_list": "",
            "testapp_dragonfly_create": "create/",
            "testapp_dragonfly_detail": "<str:pk>/",
            "testapp_dragonfly_delete": "<str:pk>/delete/",
            "testapp_dragonfly_update": "<str:pk>/update/",
            "testapp_dragonfly_extra": "extra/<str:pk>/<str:special>/",
        }

        for url in DragonflyViewSet().get_urls():
            self.assertEqual(str(url.pattern), expected[url.name])

    def test_links_that_do_not_require_an_instance(self):
        links = DragonflyViewSet().links
        self.assertEqual(get_link_url(None, links["list"]), "/dragonfly/")
        self.assertEqual(get_link_url(None, links["create"]), "/dragonfly/create/")

    def test_links_that_do_not_require_an_instance_work_if_one_is_supplied(self):
        links = DragonflyViewSet().links
        instance = Dragonfly(pk=123)
        self.assertEqual(get_link_url(None, links["list"], instance), "/dragonfly/")
        self.assertEqual(
            get_link_url(None, links["create"], instance), "/dragonfly/create/"
        )

    def test_links_that_require_an_instance(self):
        links = DragonflyViewSet().links
        instance = Dragonfly(pk=123)
        self.assertEqual(
            get_link_url(None, links["detail"], instance), "/dragonfly/123/"
        )
        self.assertEqual(
            get_link_url(None, links["update"], instance), "/dragonfly/123/update/"
        )
        self.assertEqual(
            get_link_url(None, links["delete"], instance), "/dragonfly/123/delete/"
        )

    def test_links_that_require_an_instance_raise_if_missing(self):
        links = DragonflyViewSet().links
        with self.assertRaises(NoReverseMatch):
            get_link_url(None, links["detail"], None)
        with self.assertRaises(NoReverseMatch):
            get_link_url(None, links["update"], None)
        with self.assertRaises(NoReverseMatch):
            get_link_url(None, links["delete"], None)

    def test_component_url_with_extra_context(self):
        instance = Dragonfly(pk=123)
        link = DragonflyViewSet().links["extra"]
        self.assertEqual(
            get_link_url(None, link, instance, special="param"),
            "/dragonfly/extra/123/param/",
        )

    def test_component_url_kwarg_from_request(self):
        class request:
            class resolver_match:
                kwargs = {"special": "from_request"}

        instance = Dragonfly(pk=123)
        url = DragonflyViewSet().links["extra"].reverse(instance, request)
        self.assertEqual(
            url,
            "/dragonfly/extra/123/from_request/",
        )

    def test_get_url_for_related_raises_if_missing_params(self):
        instance = Dragonfly(pk=123)
        with self.assertRaises(NoReverseMatch):
            get_url_for_related({}, instance, "extra")

    @override_settings(ROOT_URLCONF=__name__)
    @mock.patch.object(DragonflyViewSet, "url_namespace", "my_namespace")
    def test_namespace_urls(self):
        links = DragonflyViewSet().links
        instance = Dragonfly(pk=123)
        self.assertEqual(
            get_link_url(None, links["detail"], instance), "/dragonfly/123/"
        )
        self.assertEqual(
            get_link_url(None, links["update"], instance), "/dragonfly/123/update/"
        )
        self.assertEqual(
            get_link_url(None, links["delete"], instance), "/dragonfly/123/delete/"
        )
        self.assertEqual(get_link_url(None, links["list"]), "/dragonfly/")
        self.assertEqual(get_link_url(None, links["create"]), "/dragonfly/create/")

        self.assertEqual(reverse("my_namespace:testapp_dragonfly_list"), "/dragonfly/")

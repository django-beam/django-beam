from django.test import RequestFactory, TestCase
from django.urls import NoReverseMatch
from test_views import user_with_perms
from testapp.models import Dragonfly
from testapp.views import DragonflyViewSet

from beam.templatetags.beam_tags import (
    _add_params_to_url_if_new,
    get_visible_links,
    preserve_query_string,
)


class TagsTest(TestCase):
    def test_preserve_query_string_preserves_query_string(self):
        request = RequestFactory().get("/", data={"a": "b"})
        query = preserve_query_string({"request": request}, page="1")
        self.assertEqual(query, "?a=b&page=1")

    def test_preserve_query_string_works_with_mulitple_arguments(self):
        request = RequestFactory().get("/", data={"a": ["b", "c"]})
        query = preserve_query_string({"request": request}, page="1")
        self.assertEqual(query, "?a=b&a=c&page=1")

    def test_add_url_params_works(self):
        url = "https://example.com"
        self.assertEqual(
            _add_params_to_url_if_new(url, {"foo": "bar"}),
            "https://example.com?foo=bar",
        )

    def test_add_url_params_preserves_existing(self):
        url = "https://example.com?one=1"
        self.assertEqual(
            _add_params_to_url_if_new(url, {"foo": "bar"}),
            "https://example.com?foo=bar&one=1",
        )

    def test_add_url_params_prefers_existing(self):
        url = "https://example.com?one=1"
        self.assertEqual(
            _add_params_to_url_if_new(url, {"one": "2"}), "https://example.com?one=1"
        )

    def test_get_visible_links_raises(self):
        with self.assertRaises(NoReverseMatch):
            get_visible_links(
                context={},
                user=user_with_perms(["testapp.view_dragonfly"]),
                links=DragonflyViewSet().links,
                link_layout=["detail"],
                obj=None,
            )

    def test_get_visible_links_checks_permission(self):
        links = get_visible_links(
            context={},
            user=user_with_perms(["testapp.view_dragonfly", "testapp.add_dragonfly"]),
            links=DragonflyViewSet().links,
            link_layout=["detail", "update", "create"],
            obj=Dragonfly(pk=123),
        )
        self.assertEqual(
            {component.name for component, url in links}, {"create", "detail"}
        )

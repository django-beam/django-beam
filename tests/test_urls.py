from beam.templatetags.beam_tags import get_link_url
from pytest import mark
from testapp.models import Dragonfly
from testapp.views import DragonflyViewSet


def test_get_urls_produces_urls():
    assert len(DragonflyViewSet().get_urls()) == 6


expected_component_names = ["list", "detail", "update", "create", "delete"]


@mark.parametrize("component_name", expected_component_names)
def test_get_links_contains_all_view_types(component_name):
    assert component_name in DragonflyViewSet().links


urls = {
    "testapp_dragonfly_list": "",
    "testapp_dragonfly_detail": "<str:pk>/",
    "testapp_dragonfly_delete": "<str:pk>/delete/",
    "testapp_dragonfly_update": "<str:pk>/update/",
}


@mark.parametrize("url", urls.items())
def test_list_url(url):
    urlpattern = next(filter(lambda p: p.name == url[0], DragonflyViewSet().get_urls()))
    assert str(urlpattern.pattern) == url[1]


view_types_which_require_object_to_link = {
    "update": "/dragonfly/123/update/",
    "detail": "/dragonfly/123/",
    "delete": "/dragonfly/123/delete/",
}


view_types_which_require_no_object_to_link = {
    "create": "/dragonfly/create/",
    "list": "/dragonfly/",
}


@mark.parametrize("view_type, url", view_types_which_require_no_object_to_link.items())
def test_get_link_urls_that_require_object(view_type, url):
    link = dict(DragonflyViewSet().links)[view_type]
    assert get_link_url(link, None) == url


@mark.parametrize("view_type", view_types_which_require_object_to_link.keys())
def test_get_link_urls_with_missing_object(view_type):
    link = dict(DragonflyViewSet().links)[view_type]
    assert get_link_url(link, None) is None


@mark.parametrize("view_type, url", view_types_which_require_object_to_link.items())
def test_get_link_urls_that_require_object(view_type, url):
    instance = Dragonfly(pk=123)
    link = dict(DragonflyViewSet().links)[view_type]
    assert get_link_url(link, instance) == url


@mark.parametrize("view_type, url", view_types_which_require_no_object_to_link.items())
def test_get_link_urls_that_require_object(view_type, url):
    instance = Dragonfly(pk=123)
    link = dict(DragonflyViewSet().links)[view_type]
    assert get_link_url(link, instance) == url


def test_component_url_with_extra_context():
    instance = Dragonfly(pk=123)
    link = DragonflyViewSet().links["extra"]
    assert (
        get_link_url(link, instance, special="param") == "/dragonfly/extra/123/param/"
    )

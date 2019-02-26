from typing import List, Tuple, Dict
from unittest.mock import Mock
import pytest

from beam.components import Component, BaseComponent
from beam.viewsets import BaseViewSet, undefined


def test_get_components():
    class ViewSet(BaseViewSet):
        model = Mock()
        view_class = Mock()

        def get_component_classes(self):
            return super().get_component_classes() + [("test", Component)]

    assert len(ViewSet().components) == 1


def test_links():
    class ViewSet(BaseViewSet):
        model = Mock()
        view_class = Mock()

        def get_component_classes(self):
            return super().get_component_classes() + [("test", Component)]

        @property
        def links(self) -> Dict[str, BaseComponent]:
            super_links = super().links
            super_links["extra"] = Mock()
            return super_links

    links = ViewSet().links
    assert len(links) == 2
    assert "extra" in links
    assert "test" in links


def test_get_urls():
    class ViewSet(BaseViewSet):
        model = Mock()
        view_class = Mock()

        def get_component_classes(self):
            return super().get_component_classes() + [("test", Component)]

        url = "foo/<pk>"

    urls = ViewSet().get_urls()

    assert len(urls) == 1
    assert urls[0].pattern._route == "foo/<pk>"


def test_get_view():
    class ViewSet(BaseViewSet):
        model = Mock()
        view_class = Mock()

        def get_component_classes(self):
            return super().get_component_classes() + [("test", Component)]

        url = "foo/<pk>"

    viewset = ViewSet()
    component = viewset.components["test"]

    assert viewset._get_view(component).__wrapped__ == ViewSet.view_class.as_view()


def test_resolve_component_kwargs():
    class ViewSet(BaseViewSet):
        model = Mock()
        view_class = Mock()
        arg = "value"

    assert ViewSet()._resolve_component_kwargs("test", ["arg"])["arg"] == "value"


def test_resolve_component_kwargs_does_not_return_unspecified_value():
    class ViewSet(BaseViewSet):
        model = Mock()
        view_class = Mock()

    component = Mock()
    component.get_arguments.return_value = ["arg"]

    assert "arg" not in ViewSet()._resolve_component_kwargs("test", ["arg"])


def test_resolve_component_kwargs_does_not_return_sentinel_value():
    class ViewSet(BaseViewSet):
        model = Mock()
        view_class = Mock()
        arg = undefined

    assert "arg" not in ViewSet()._resolve_component_kwargs("test", ["arg"])


def test_resolve_component_kwargs_does_return_falsy_values():
    class ViewSet(BaseViewSet):
        model = Mock()
        view_class = Mock()
        arg = None

    assert ViewSet()._resolve_component_kwargs("test", ["arg"])["arg"] == None


def test_resolve_component_kwargs_prefers_specific():
    class ViewSet(BaseViewSet):
        model = Mock()
        view_class = Mock()
        arg = "value"
        test_arg = "specific_value"

    assert (
        ViewSet()._resolve_component_kwargs("test", ["arg"])["arg"] == "specific_value"
    )


def test_resolve_component_kwargs_does_not_return_specific_undefined():
    class ViewSet(BaseViewSet):
        model = Mock()
        view_class = Mock()
        arg = "value"
        test_arg = undefined

    assert ViewSet()._resolve_component_kwargs("test", ["arg"])["arg"] == "value"


def test_resolve_component_kwargs_prefers_specific_falsy():
    class ViewSet(BaseViewSet):
        model = Mock()
        view_class = Mock()
        arg = "value"
        test_arg = None

    assert ViewSet()._resolve_component_kwargs("test", ["arg"])["arg"] == None

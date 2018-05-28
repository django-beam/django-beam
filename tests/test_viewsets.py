import pytest
from beam.viewsets import ViewSet, default_registry

from testapp.views import DragonflyViewSet


def test_registry_contains_viewset():
    assert default_registry["testapp"]["dragonfly"] is DragonflyViewSet


def test_duplicate_registration_errors():
    with pytest.raises(Exception):

        class AnotherDragonFlyViewSet(DragonflyViewSet):
            pass


def test_context_items_are_passed_to_viewset_context():

    class TestViewSet(ViewSet):
        context_items = ["foo"]
        foo = "attr-foo"

    context = TestViewSet()._get_viewset_context("create", request=None)
    assert context["foo"] == "attr-foo"


def test_non_context_attributes_are_not_passed_to_viewset_context():

    class TestViewSet(ViewSet):
        context_items = []
        foo = "attr-foo"

    context = TestViewSet()._get_viewset_context("create", request=None)
    assert "foo" not in context


def test_context_items_prefer_getter_over_attribute():

    class TestViewSet(ViewSet):
        context_items = ["foo"]
        foo = "attr-foo"

        def get_foo(self, request):
            return "get-foo"

    context = TestViewSet()._get_viewset_context("create", request=object())
    assert context["foo"] == "get-foo"


def test_context_items_prefer_specific_attribute_over_getter():

    class TestViewSet(ViewSet):
        context_items = ["foo"]

        def get_foo(self, request):
            return "attr-foo"

        create_foo = "create-attr-foo"

    context = TestViewSet()._get_viewset_context("create", request=object())
    assert context["foo"] == "create-attr-foo"


def test_context_items_prefer_specific_getter_over_specific_attribute():

    class TestViewSet(ViewSet):
        context_items = ["foo"]

        def get_create_foo(self, request):
            return "get-create-foo"

        create_foo = "create-attr-foo"

    context = TestViewSet()._get_viewset_context("create", request=object())
    assert context["foo"] == "get-create-foo"


def test_missing_context_items_are_not_passed():

    class TestViewSet(ViewSet):
        context_items = ["foo", "bar"]
        foo = "foo"

    context = TestViewSet()._get_viewset_context("create", request=object())
    assert "foo" in context
    assert "bar" not in context

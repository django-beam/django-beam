from beam.viewsets import ViewSet


def test_context_items_are_passed_to_viewset_context():

    class TestViewSet(ViewSet):
        context_items = ["foo"]
        foo = "attr-foo"

    context = TestViewSet()._get_viewset_context("create")
    assert context["foo"] == "attr-foo"


def test_non_context_attributes_are_not_passed_to_viewset_context():

    class TestViewSet(ViewSet):
        context_items = []
        foo = "attr-foo"

    context = TestViewSet()._get_viewset_context("create")
    assert "foo" not in context


def test_context_items_prefer_getter_over_attribute():

    class TestViewSet(ViewSet):
        context_items = ["foo"]
        foo = "attr-foo"

        def get_foo(self):
            return "get-foo"

    context = TestViewSet()._get_viewset_context("create")
    assert context["foo"] == "get-foo"


def test_context_items_prefer_specific_attribute_over_getter():

    class TestViewSet(ViewSet):
        context_items = ["foo"]

        def get_foo(self):
            return "attr-foo"

        create_foo = "create-attr-foo"

    context = TestViewSet()._get_viewset_context("create")
    assert context["foo"] == "create-attr-foo"


def test_context_items_prefer_specific_getter_over_specific_attribute():

    class TestViewSet(ViewSet):
        context_items = ["foo"]

        def get_create_foo(self):
            return "get-create-foo"

        create_foo = "create-attr-foo"

    context = TestViewSet()._get_viewset_context("create")
    assert context["foo"] == "get-create-foo"


def test_missing_context_items_are_not_passed():

    class TestViewSet(ViewSet):
        context_items = ["foo", "bar"]
        foo = "foo"

    context = TestViewSet()._get_viewset_context("create")
    assert "foo" in context
    assert "bar" not in context

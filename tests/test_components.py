from unittest import TestCase
from unittest.mock import Mock

from testapp.views import DragonflyViewSet

from beam.components import BaseComponent, Component


class ComponentTest(TestCase):
    def test_component_with_queryset_guesses_model(self):
        queryset = Mock()
        assert (
            Component(name="test", queryset=queryset, view_class=Mock()).model
            == queryset.model
        )

    def test_component_with_queryset_copies_queryset(self):
        queryset = Mock()
        assert (
            Component(name="test", queryset=queryset, view_class=Mock()).queryset
            is not queryset
        )

    def test_component_with_model_guesses_queryset(self):
        model = Mock()
        assert (
            Component(name="test", model=model, view_class=Mock()).queryset
            == model._default_manager.all()
        )

    def test_component_without_verbose_name_guesses_name(self):
        model = Mock()
        assert (
            Component(name="test", model=model, view_class=Mock()).queryset
            == model._default_manager.all()
        )

    def test_base_component_requires_a_name(self):
        with self.assertRaises(ValueError):
            BaseComponent()
        BaseComponent(name="foo")

    def test_component_requires_one_of_model_or_queryset(self):
        with self.assertRaises(ValueError):
            Component(name="foo", view_class=Mock())
        Component(name="foo", model=Mock(), view_class=Mock())
        Component(name="foo", queryset=Mock(), view_class=Mock())

    def test_component_requires_a_view_class(self):
        with self.assertRaises(ValueError):
            Component(name="foo", model=Mock())
        Component(name="foo", model=Mock(), view_class=Mock())

    def test_arguments_are_collected(self):
        class SubComponent(Component):
            def __init__(self, new_arg_1=None, **kwargs):
                super().__init__(**kwargs)

        class SubSubComponent(SubComponent):
            def __init__(self, new_arg_2=None, **kwargs):
                super().__init__(**kwargs)

        assert "new_arg_1" in SubComponent.get_arguments()
        assert "new_arg_2" not in SubComponent.get_arguments()

        assert "new_arg_1" in SubSubComponent.get_arguments()
        assert "new_arg_2" in SubSubComponent.get_arguments()

    def test_component_has_a_sensible_string_representation(self):
        self.assertEqual(
            str(DragonflyViewSet().links["detail"]),
            "<Component testapp.views.DragonflyViewSet 'detail'>",
        )

    def test_component_has_a_sensible_string_representation_without_viewset(self):
        self.assertEqual(
            str(BaseComponent(viewset=None, name="detail")),
            "<BaseComponent 'detail'>",
        )

from unittest.mock import Mock
import pytest


from beam.components import Component, BaseComponent


def test_component_with_queryset_guesses_model():
    queryset = Mock()
    assert (
        Component(name="test", queryset=queryset, view_class=Mock()).model
        == queryset.model
    )


def test_component_with_model_guesses_queryset():
    model = Mock()
    assert (
        Component(name="test", model=model, view_class=Mock()).queryset
        == model._default_manager.all()
    )


def test_component_without_verbose_name_guesses_name():
    model = Mock()
    assert (
        Component(name="test", model=model, view_class=Mock()).queryset
        == model._default_manager.all()
    )


def test_base_component_requires_a_name():
    with pytest.raises(ValueError):
        BaseComponent()
    BaseComponent(name="foo")


def test_component_requires_one_of_model_or_queryset():
    with pytest.raises(ValueError):
        Component(name="foo", view_class=Mock())
    Component(name="foo", model=Mock(), view_class=Mock())
    Component(name="foo", queryset=Mock(), view_class=Mock())


def test_component_requires_a_view_class():
    with pytest.raises(ValueError):
        Component(name="foo", model=Mock())
    Component(name="foo", model=Mock(), view_class=Mock())


def test_arguments_are_collected():
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

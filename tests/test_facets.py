from unittest import TestCase
from unittest.mock import Mock

from testapp.views import DragonflyViewSet

from beam.facets import BaseFacet, Facet


class FacetTest(TestCase):
    def test_facet_with_queryset_guesses_model(self):
        queryset = Mock()
        assert (
            Facet(name="test", queryset=queryset, view_class=Mock()).model
            == queryset.model
        )

    def test_facet_with_queryset_copies_queryset(self):
        queryset = Mock()
        assert (
            Facet(name="test", queryset=queryset, view_class=Mock()).queryset
            is not queryset
        )

    def test_facet_with_model_guesses_queryset(self):
        model = Mock()
        assert (
            Facet(name="test", model=model, view_class=Mock()).queryset
            == model._default_manager.all()
        )

    def test_facet_without_verbose_name_guesses_name(self):
        model = Mock()
        assert (
            Facet(name="test", model=model, view_class=Mock()).queryset
            == model._default_manager.all()
        )

    def test_base_facet_requires_a_name(self):
        with self.assertRaises(ValueError):
            BaseFacet()
        BaseFacet(name="foo")

    def test_facet_requires_one_of_model_or_queryset(self):
        with self.assertRaises(ValueError):
            Facet(name="foo", view_class=Mock())
        Facet(name="foo", model=Mock(), view_class=Mock())
        Facet(name="foo", queryset=Mock(), view_class=Mock())

    def test_facet_requires_a_view_class(self):
        with self.assertRaises(ValueError):
            Facet(name="foo", model=Mock())
        Facet(name="foo", model=Mock(), view_class=Mock())

    def test_arguments_are_collected(self):
        class SubFacet(Facet):
            def __init__(self, new_arg_1=None, **kwargs):
                super().__init__(**kwargs)

        class SubSubFacet(SubFacet):
            def __init__(self, new_arg_2=None, **kwargs):
                super().__init__(**kwargs)

        assert "new_arg_1" in SubFacet.get_arguments()
        assert "new_arg_2" not in SubFacet.get_arguments()

        assert "new_arg_1" in SubSubFacet.get_arguments()
        assert "new_arg_2" in SubSubFacet.get_arguments()

    def test_facet_has_a_sensible_string_representation(self):
        self.assertEqual(
            str(DragonflyViewSet().links["detail"]),
            "<Facet testapp.views.DragonflyViewSet 'detail'>",
        )

    def test_facet_has_a_sensible_string_representation_without_viewset(self):
        self.assertEqual(
            str(BaseFacet(viewset=None, name="detail")),
            "<BaseFacet 'detail'>",
        )

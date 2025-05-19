from typing import Dict
from unittest.mock import Mock

from django.test import TestCase

from beam.facets import BaseFacet, Facet
from beam.viewsets import BaseViewSet, undefined


class ViewsetTest(TestCase):
    def test_get_facets(self):
        class ViewSet(BaseViewSet):
            model = Mock()
            view_class = Mock()

            def get_facet_classes(self):
                return super().get_facet_classes() + [("test", Facet)]

        self.assertEqual(len(ViewSet().facets), 1)

    def test_links(self):
        class ViewSet(BaseViewSet):
            model = Mock()
            view_class = Mock()

            def get_facet_classes(self):
                return super().get_facet_classes() + [("test", Facet)]

            @property
            def links(self) -> Dict[str, BaseFacet]:
                super_links = super().links
                super_links["extra"] = Mock()
                return super_links

        links = ViewSet().links
        assert len(links) == 2
        self.assertEqual(len(links), 2)
        self.assertIn("extra", links)
        self.assertIn("test", links)

    def test_get_urls(self):
        class ViewSet(BaseViewSet):
            model = Mock()
            view_class = Mock()

            def get_facet_classes(self):
                return super().get_facet_classes() + [("test", Facet)]

            url = "foo/<pk>"

        urls = ViewSet().get_urls()

        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0].pattern._route, "foo/<pk>")

    def test_get_view(self):
        class ViewSet(BaseViewSet):
            model = Mock()
            view_class = Mock()

            def get_facet_classes(self):
                return super().get_facet_classes() + [("test", Facet)]

            url = "foo/<pk>"

        viewset = ViewSet()
        facet = viewset.facets["test"]

        self.assertEqual(
            viewset._get_view(facet).__wrapped__, ViewSet.view_class.as_view()
        )

    def test_resolve_facet_kwargs(self):
        class ViewSet(BaseViewSet):
            model = Mock()
            view_class = Mock()
            arg = "value"

        self.assertEqual(
            ViewSet()._resolve_facet_kwargs("test", ["arg"])["arg"], "value"
        )

    def test_resolve_facet_kwargs_does_not_return_unspecified_value(self):
        class ViewSet(BaseViewSet):
            model = Mock()
            view_class = Mock()

        facet = Mock()
        facet.get_arguments.return_value = ["arg"]

        self.assertNotIn("arg", ViewSet()._resolve_facet_kwargs("test", ["arg"]))

    def test_resolve_facet_kwargs_does_not_return_sentinel_value(self):
        class ViewSet(BaseViewSet):
            model = Mock()
            view_class = Mock()
            arg = undefined

        self.assertNotIn("arg", ViewSet()._resolve_facet_kwargs("test", ["arg"]))

    def test_resolve_facet_kwargs_does_return_falsy_values(self):
        class ViewSet(BaseViewSet):
            model = Mock()
            view_class = Mock()
            arg = None

        self.assertIsNone(ViewSet()._resolve_facet_kwargs("test", ["arg"])["arg"])

    def test_resolve_facet_kwargs_prefers_specific(self):
        class ViewSet(BaseViewSet):
            model = Mock()
            view_class = Mock()
            arg = "value"
            test_arg = "specific_value"

        self.assertEqual(
            ViewSet()._resolve_facet_kwargs("test", ["arg"])["arg"],
            "specific_value",
        )

    def test_resolve_facet_kwargs_does_not_return_specific_undefined(self):
        class ViewSet(BaseViewSet):
            model = Mock()
            view_class = Mock()
            arg = "value"
            test_arg = undefined

        self.assertEqual(
            ViewSet()._resolve_facet_kwargs("test", ["arg"])["arg"], "value"
        )

    def test_resolve_facet_kwargs_prefers_specific_falsy(self):
        class ViewSet(BaseViewSet):
            model = Mock()
            view_class = Mock()
            arg = "value"
            test_arg = None

        self.assertIsNone(ViewSet()._resolve_facet_kwargs("test", ["arg"])["arg"])

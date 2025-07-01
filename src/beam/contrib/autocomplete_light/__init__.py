from typing import List

from dal import autocomplete
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from beam.facets import Facet
from beam.urls import UrlKwargDict
from beam.views import FacetMixin
from beam.viewsets import BaseViewSet


class BaseAutocomplete(FacetMixin, autocomplete.Select2QuerySetView):
    @property
    def lookup_type(self):
        return self.facet.autocomplete_lookup_type

    @property
    def search_fields(self):
        return self.facet.autocomplete_search_fields

    def get_result_label(self, item):
        formatter = self.facet.autocomplete_result_label
        if formatter:
            return formatter(item)
        return super().get_result_label(item)

    @property
    def model(self):
        return self.facet.model

    def get_queryset(self):
        qs = self.facet.queryset
        return self.filter_words(self.q, qs)

    def filter_words(self, q, qs):
        assert self.search_fields

        if not q:
            return qs

        if self.lookup_type in ("contains", "icontains"):
            words = self.q.split(" ")
        else:
            words = [self.q]

        qs_filter = Q()
        for word in words:
            word = word.strip()
            if not word:
                continue

            q = Q()
            for field in self.search_fields:
                q |= Q(**{"{}__{}".format(field, self.lookup_type): word})

            qs_filter &= q

        return qs.filter(qs_filter)


class AutocompleteFacet(Facet):
    def __init__(
        self,
        autocomplete_search_fields=None,
        autocomplete_result_label=None,
        autocomplete_lookup_type="istartswith",
        **kwargs
    ):
        self.autocomplete_search_fields = autocomplete_search_fields
        self.autocomplete_result_label = autocomplete_result_label
        self.autocomplete_lookup_type = autocomplete_lookup_type
        super().__init__(**kwargs)
        self.show_link = False


class AutocompleteMixin(BaseViewSet):
    """
    A viewset mixin that provides a autocomplete url for the model

    Use `autocomplete_search_fields` to specify the fields to be searched.
    Provide a callable `autocomplete_result_label` that maps results to strings if you want
    to change the string representation of the items.

    """

    autocomplete_view_class = BaseAutocomplete
    autocomplete_url = "autocomplete/"
    autocomplete_url_kwargs: UrlKwargDict = {}
    autocomplete_url_name = None
    autocomplete_verbose_name = _("autocomplete")

    autocomplete_lookup_type = "istartswith"
    autocomplete_search_fields: List[str] = []
    autocomplete_result_label = None
    autocomplete_permission = "{app_label}.view_{model_name}"

    def get_facet_classes(self):
        return [("autocomplete", AutocompleteFacet)] + super().get_facet_classes()

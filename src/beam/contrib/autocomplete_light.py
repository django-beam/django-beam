from dal import autocomplete
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from beam.views import ViewSetContextMixin
from beam.viewsets import BaseViewSet


class BaseAutocomplete(ViewSetContextMixin, autocomplete.Select2QuerySetView):
    @property
    def search_fields(self):
        return self.viewset_context["autocomplete_search_fields"]

    def get_result_label(self, item):
        formatter = self.viewset_context.get("autocomplete_result_label")
        if formatter:
            return formatter(item)
        return super().get_result_label(item)

    @property
    def model(self):
        if self.viewset_context["model"] is not None:
            return self.viewset_context["model"]
        return super().model

    def get_queryset(self):
        qs = self.viewset_context["queryset"]

        if not qs:
            qs = self.model._default_manager.all()

        return self.filter_words(self.q, qs)

    def filter_words(self, q, qs):
        assert self.search_fields

        if not q:
            return qs

        qs_filter = Q()
        for word in self.q.split(" "):
            word = word.strip()
            if not word:
                continue

            q = Q()
            for field in self.search_fields:
                q |= Q(**{"{}__istartswith".format(field): word})

            qs_filter &= q

        return qs.filter(qs_filter)


class AutocompleteMixin(BaseViewSet):
    """
    A viewset mixin that provides a autocomplete url for the model

    Use `autocomplete_search_fields` to specify the fields to be searched.
    Provide a callable `autocomplete_result_label` that maps results to strings if you want
    to change the string representation of the items.

    """

    autocomplete_view_class = BaseAutocomplete
    autocomplete_url = "autocomplete/"
    autocomplete_verbose_name = _("autocomplete")

    autocomplete_search_fields = None
    autocomplete_result_label = None

    def get_context_items(self):
        return super().get_context_items() + [
            "autocomplete_search_fields",
            "autocomplete_result_label",
        ]

    def get_view_types(self):
        return ["autocomplete"] + super().get_view_types()

    def _get_link(self, view_type):
        if view_type == "autocomplete":
            return None
        return super()._get_link(view_type)

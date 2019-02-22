from django.forms import all_valid
from django.shortcuts import redirect
from extra_views import SearchableListMixin
from extra_views.contrib.mixins import VALID_STRING_LOOKUPS

from beam.registry import register
from beam.viewsets import default_registry
from django.apps import apps
from django.views import generic
from django.views.generic.base import ContextMixin, TemplateView


class ViewSetContextMixin(ContextMixin):
    viewset_context = None
    links = None
    hidden_links = None
    visible_links = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "viewset_context" not in context:
            context["viewset_context"] = self.viewset_context
        if "links" not in context:
            context["links"] = self.links
        if "hidden_links" not in context:
            context["hidden_links"] = self.get_hidden_links()
        if "visible_links" not in context:
            context["visible_links"] = self.visible_links
        return context

    def get_hidden_links(self):
        # default to hiding link to self
        if self.hidden_links is not None:
            return self.hidden_links
        return [self.viewset_context["view_type"]]

    @property
    def model(self):
        if self.viewset_context["model"] is not None:
            return self.viewset_context["model"]
        return super().model

    def get_queryset(self):
        if self.viewset_context["queryset"] is not None:
            return self.viewset_context["queryset"]
        return super().get_queryset()

    def get_form_class(self):
        if self.viewset_context["form_class"] is not None:
            return self.viewset_context["form_class"]
        return super().get_form_class()

    @property
    def fields(self):
        if self.viewset_context["fields"] is not None:
            return self.viewset_context["fields"]
        return super().fields

    def get_inline_classes(self):
        if self.viewset_context["inline_classes"] is not None:
            return self.viewset_context["inline_classes"]
        return super().get_inline_classes()


class InlinesMixin(ContextMixin):
    inline_classes = []

    def get_inline_classes(self):
        return self.inline_classes

    def get_inlines(self, object=None):
        inlines = []
        for inline_class in self.get_inline_classes():
            inlines.append(
                inline_class(
                    parent_instance=object if object is not None else self.object,
                    parent_model=self.model,
                    request=self.request,
                )
            )
        return inlines

    def get_context_data(self, **kwargs):
        if "inlines" not in kwargs:
            kwargs["inlines"] = self.get_inlines()
        return super().get_context_data(**kwargs)


class CreateWithInlinesMixin(InlinesMixin):
    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            # we have to make sure that the same instance is used for form and inlines
            inlines = self.get_inlines(object=form.save(commit=False))
        else:
            inlines = self.get_inlines()

        if all_valid(inline.formset for inline in inlines) and form.is_valid():
            return self.form_valid(form, inlines)

        return self.form_invalid(form, inlines)

    def form_valid(self, form, inlines):
        self.object = form.save()
        for inline in inlines:
            inline.formset.save()
        return redirect(self.get_success_url())

    def form_invalid(self, form, inlines):
        return self.render_to_response(
            self.get_context_data(form=form, inlines=inlines)
        )


class UpdateWithInlinesMixin(InlinesMixin):
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        inlines = self.get_inlines()

        if form.is_valid() and all_valid(inline.formset for inline in inlines):
            return self.form_valid(form, inlines)

        return self.form_invalid(form, inlines)

    def form_valid(self, form, inlines):
        self.object = form.save()
        for inline in inlines:
            inline.formset.save()
        return redirect(self.get_success_url())

    def form_invalid(self, form, inlines):
        return self.render_to_response(
            self.get_context_data(form=form, inlines=inlines)
        )


class CreateView(ViewSetContextMixin, CreateWithInlinesMixin, generic.CreateView):
    def get_template_names(self):
        return super().get_template_names() + ["beam/create.html"]

    def get_success_url(self):
        return self.links["detail"].get_url(obj=self.object)


class UpdateView(ViewSetContextMixin, UpdateWithInlinesMixin, generic.UpdateView):
    hidden_links = ["create", "update"]

    def get_template_names(self):
        return super().get_template_names() + ["beam/update.html"]

    def get_success_url(self):
        return self.links["detail"].get_url(obj=self.object)


class ListView(SearchableListMixin, ViewSetContextMixin, generic.ListView):
    @property
    def search_fields(self):
        if self.viewset_context["list_search_fields"] is not None:
            return self.viewset_context["list_search_fields"]
        return None

    def get_paginate_by(self, queryset):
        if self.viewset_context["list_paginate_by"] is not None:
            return self.viewset_context["list_paginate_by"]
        return super().get_paginate_by(queryset)

    def get_search_query(self):
        if not self.search_fields:
            return ""
        return super().get_search_query()

    def get_template_names(self):
        return super().get_template_names() + ["beam/list.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.get_search_query()
        return context


class DetailView(ViewSetContextMixin, InlinesMixin, generic.DetailView):
    hidden_links = ["detail", "delete"]

    def get_template_names(self):
        return super().get_template_names() + ["beam/detail.html"]


class DeleteView(ViewSetContextMixin, InlinesMixin, generic.DeleteView):
    def get_template_names(self):
        return super().get_template_names() + ["beam/delete.html"]

    def get_success_url(self):
        return self.links["list"].get_url()


class DashboardView(TemplateView):
    template_name = "beam/dashboard.html"

    viewsets = None
    registry = default_registry

    def build_registry(self, viewsets):
        registry = {}
        for viewset in viewsets:
            register(registry, viewset)
        return registry

    def get_registry(self):
        if self.viewsets:
            return self.build_registry(self.viewsets)
        else:
            return self.registry

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        grouped = []
        for app_label, viewsets_dict in self.get_registry().items():
            group = {
                "app_label": app_label,
                "app_config": apps.get_app_config(app_label),
                "viewsets": viewsets_dict.values(),
            }
            grouped.append(group)
        context["grouped_by_app"] = grouped
        return context

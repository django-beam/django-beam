from typing import List, Type

from django.apps import apps
from django.forms import all_valid
from django.shortcuts import redirect
from django.views import generic
from django.views.generic.base import ContextMixin, TemplateView
from extra_views import SearchableListMixin

from beam.registry import register, default_registry
from .inlines import RelatedInline


class ViewSetContextMixin(ContextMixin):
    component = None
    viewset = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["viewset"] = self.viewset
        context["component"] = self.component

        return context

    @property
    def model(self):
        return self.component.model

    def get_queryset(self):
        return self.component.queryset

    def get_form_class(self):
        if self.component.form_class:
            return self.component.form_class
        return super().get_form_class()

    @property
    def fields(self):
        if self.component.fields:
            return self.component.fields
        return super().fields

    def get_inline_classes(self):
        return self.component.inline_classes


class InlinesMixin(ContextMixin):
    inline_classes: List[Type[RelatedInline]] = []

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
        return self.viewset.links["detail"].reverse(obj=self.object)


class UpdateView(ViewSetContextMixin, UpdateWithInlinesMixin, generic.UpdateView):
    def get_template_names(self):
        return super().get_template_names() + ["beam/update.html"]

    def get_success_url(self):
        return self.viewset.links["detail"].reverse(obj=self.object)


class ListView(SearchableListMixin, ViewSetContextMixin, generic.ListView):
    @property
    def search_fields(self):
        return self.component.list_search_fields

    def get_paginate_by(self, queryset):
        return self.component.list_paginate_by

    def get_search_query(self):
        if not self.search_fields:
            return ""
        return super().get_search_query()

    def get_template_names(self):
        return super().get_template_names() + ["beam/list.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.get_search_query()
        context["list_item_link_layout"] = self.component.list_item_link_layout
        return context


class DetailView(ViewSetContextMixin, InlinesMixin, generic.DetailView):
    def get_template_names(self):
        return super().get_template_names() + ["beam/detail.html"]


class DeleteView(ViewSetContextMixin, InlinesMixin, generic.DeleteView):
    def get_template_names(self):
        return super().get_template_names() + ["beam/delete.html"]

    def get_success_url(self):
        return self.viewset.links["list"].reverse()


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

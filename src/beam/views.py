from typing import List, Optional, Type

from django.apps import apps
from django.contrib import messages
from django.contrib.admin.utils import NestedObjects
from django.core.exceptions import FieldDoesNotExist, PermissionDenied
from django.db import router
from django.forms import all_valid
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.html import escape
from django.utils.translation import gettext as _
from django.views import generic
from django.views.generic.base import ContextMixin, TemplateView
from django_filters.filterset import filterset_factory
from extra_views import SearchableListMixin

from beam.registry import default_registry, register

from .actions import Action
from .components import Component, ListComponent
from .inlines import RelatedInline


class ComponentMixin(ContextMixin):
    component: Optional[Component] = None
    viewset = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["viewset"] = self.viewset
        context["component"] = self.component
        context["popup"] = self.request.GET.get("_popup")

        return context

    @property
    def model(self):
        return self.component.model

    def get_queryset(self):
        return self.component.queryset

    def get_form_class(self):
        if getattr(self.component, "form_class", None):
            return self.component.form_class
        return super().get_form_class()

    @property
    def fields(self):
        if self.component.fields:
            return self.component.fields
        return super().fields

    def get_inline_classes(self):
        return self.component.inline_classes

    def has_perm(self):
        try:
            obj = self.get_object()
        except AttributeError:
            obj = None
        return self.component.has_perm(self.request.user, obj)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You shall not pass")

        # Inner import to prevent django.contrib.admin (app) from
        # importing django.contrib.auth.models.User (unrelated model).
        from django.contrib.auth.views import redirect_to_login

        return redirect_to_login(self.request.get_full_path())

    def dispatch(self, request, *args, **kwargs):
        if not self.has_perm():
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


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


class CreateView(ComponentMixin, CreateWithInlinesMixin, generic.CreateView):
    def get_template_names(self):
        return super().get_template_names() + ["beam/create.html"]

    def get_success_url(self):
        return self.viewset.links["detail"].reverse(
            obj=self.object, request=self.request
        )

    def get_success_message(self):
        return _('The {model} "{name}" was added successfully.').format(
            model=self.model._meta.verbose_name,
            name=str(self.object),
        )

    def form_valid(self, form, inlines):
        response = super().form_valid(form, inlines)
        success_message = self.get_success_message()
        if success_message:
            messages.success(self.request, success_message)
        if self.request.GET.get("_popup"):
            return self.popup_response()
        return response

    def popup_response(self):
        return HttpResponse(
            "<script>"
            "window.opener.postMessage("
            '{{id: "{id}", result: "created", source: "{source}", text: "{text}"}}, '
            "document.origin"
            ");"
            "window.close()"
            "</script>".format(
                id=escape(self.object.pk),
                source=escape(self.request.GET["_popup"]),
                text=escape(str(self.object)),
            )
        )


class UpdateView(ComponentMixin, UpdateWithInlinesMixin, generic.UpdateView):
    def get_template_names(self):
        return super().get_template_names() + ["beam/update.html"]

    def get_success_message(self):
        return _('The {model} "{name}" was changed successfully.').format(
            model=self.model._meta.verbose_name,
            name=str(self.object),
        )

    def form_valid(self, form, inlines):
        response = super().form_valid(form, inlines)
        success_message = self.get_success_message()
        if success_message:
            messages.success(self.request, success_message)
        return response

    def get_success_url(self):
        if self.request.POST.get("submit", None) == "save_and_continue_editing":
            return self.request.get_full_path()
        return self.viewset.links["detail"].reverse(
            obj=self.object, request=self.request
        )


class SortableListMixin(ComponentMixin):
    sort_param = "o"
    sort_separator = ","

    def get_sort_fields(self):
        if self.component.list_sort_fields is None:
            return [
                # cast to string to support virtual fields
                str(field)
                for field in self.component.fields
                if self.get_sort_column_for_field(str(field))
            ]

        for field in self.component.list_sort_fields:
            if self.get_sort_column_for_field(field) is None:
                raise Exception(
                    "Unable to determine sort column for explicit sort field {} on {}".format(
                        field, self.viewset
                    )
                )

        return self.component.list_sort_fields

    def get_sort_fields_columns(self):
        return self.component.list_sort_fields_columns or {}

    def get_sort_column_for_field(self, field_name):
        explicit = self.get_sort_fields_columns()
        if field_name in explicit:
            return explicit[field_name]

        try:
            field = self.model._meta.get_field(field_name)
            return field.name
        except FieldDoesNotExist:
            return None

    def get_sort_fields_from_request(self) -> List[str]:
        fields = []
        sort_fields = set(self.get_sort_fields())
        for field in self.request.GET.get(self.sort_param, "").split(
            self.sort_separator
        ):
            if field.startswith("-"):
                sort_field = field[1:]
            else:
                sort_field = field

            if sort_field in sort_fields:
                fields.append(field)
        return fields

    def get_sort_columns(self, fields):
        columns = []
        for field in fields:
            if field.startswith("-"):
                descending = True
                field = field[1:]
            else:
                descending = False

            column = self.get_sort_column_for_field(field)
            if not column:
                continue

            columns.append("-" + column if descending else column)
        return columns

    def sort_queryset(self, qs):
        current_sort_fields = self.get_sort_fields_from_request()
        current_sort_columns = self.get_sort_columns(current_sort_fields)
        if current_sort_columns:
            qs = qs.order_by(*current_sort_columns)
        return qs

    def get_queryset(self):
        qs = super().get_queryset()
        return self.sort_queryset(qs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sortable_fields"] = set(self.get_sort_fields())
        context["sorted_fields"] = self.get_sort_fields_from_request()
        return context


class FiltersetMixin(ComponentMixin):
    filterset_class = None
    filterset_fields = None
    filterset = None

    def get_filterset_fields(self):
        if self.filterset_fields is not None:
            return self.filterset_fields
        return self.component.list_filterset_fields

    def get_filterset_class(self):
        if self.filterset_class:
            return self.filterset_class
        if self.component.list_filterset_class:
            return self.component.list_filterset_class
        elif self.component.list_filterset_fields:
            return filterset_factory(
                model=self.model, fields=self.get_filterset_fields()
            )
        return None

    def get_filterset_kwargs(self):
        """
        Returns the keyword arguments for instantiating the filterset.
        """
        kwargs = {
            "data": self.request.GET or None,
            "request": self.request,
            "prefix": "filter",
            "queryset": self.component.queryset,
        }
        return kwargs

    def get_filterset(self):
        filterset_class = self.get_filterset_class()
        if not filterset_class:
            return None
        return filterset_class(**self.get_filterset_kwargs())

    def get_queryset(self):
        qs = super().get_queryset()
        if self.filterset and self.filterset.is_bound and self.filterset.is_valid():
            qs = self.filterset.filter_queryset(qs)
        return qs

    def dispatch(self, request, *args, **kwargs):
        self.filterset = self.get_filterset()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filterset"] = self.filterset
        return context


class InlineActionMixin(InlinesMixin):
    def get_action_qs(self, inline):
        ids = self.request.POST.getlist("_action_select[]")
        select_across = self.request.POST.get("_action_select_across") == "all"

        objects = inline.get_queryset()
        if not select_across:
            objects = objects.filter(pk__in=ids)

        if not select_across and len(objects) != len(ids):
            messages.error(
                self.request,
                _(
                    "There was an error finding the objects you selected. "
                    "This could be caused by another user changing them concurrently. "
                    "Please try again."
                ),
            )
            return objects.none()

        return objects

    def get_action(self):
        for inline in self.get_inlines(self.get_object()):
            action = inline.get_action()
            if action and action.is_bound:
                return inline, action
        return None, None

    def handle_action(self, inline, action):
        form = action.get_form()

        if form and not form.is_valid():
            return None

        result: Optional[HttpResponse] = action.apply(
            queryset=self.get_action_qs(inline)
        )
        success_message: str = action.get_success_message()

        if success_message:
            messages.success(self.request, success_message)

        if result:
            return result

        return redirect(self.request.get_full_path())

    def post(self, request, *args, **kwargs):
        inline, action = self.get_action()
        if action:
            response = self.handle_action(inline, action)
            if response:
                return response
        return self.get(request, *args, **kwargs)


class ListActionsMixin(ComponentMixin):
    component: ListComponent

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions"] = self.actions
        return context

    def get_action_qs(self):
        ids = self.request.POST.getlist("_action_select[]")
        select_across = self.request.POST.get("_action_select_across") == "all"

        objects = self.get_queryset()
        if not select_across:
            objects = objects.filter(pk__in=ids)

        if not select_across and len(objects) != len(ids):
            messages.error(
                self.request,
                _(
                    "There was an error finding the objects you selected. "
                    "This could be caused by another user changing them concurrently. "
                    "Please try again."
                ),
            )
            return objects.none()

        return objects

    def get_actions(self):
        selected_action = self.request.POST.get("_action_choice")
        actions = []
        action_class: Type[Action]
        for index, action_class in enumerate(self.component.list_actions_classes):
            action_id = "{}-{}".format(index, action_class.name)
            action = action_class(
                data=self.request.POST if action_id == selected_action else None,
                model=self.model,
                id=action_id,
                request=self.request,
            )
            if action.has_perm(self.request.user):
                actions.append(action)
        return actions

    def get_action(self):
        for action in self.actions:
            if action.is_bound:
                return action
        return None

    def handle_action(self, action):
        form = action.get_form()

        if form and not form.is_valid():
            return None

        result: Optional[HttpResponse] = action.apply(queryset=self.get_action_qs())
        success_message: str = action.get_success_message()

        if success_message:
            messages.success(self.request, success_message)

        if result:
            return result

        return redirect(self.request.get_full_path())

    def dispatch(self, request, *args, **kwargs):
        self.actions = self.get_actions()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = self.get_action()
        if action:
            response = self.handle_action(action)
            if response:
                return response
        return self.get(request, *args, **kwargs)


class ListView(
    ListActionsMixin,
    FiltersetMixin,
    SearchableListMixin,
    SortableListMixin,
    ComponentMixin,
    generic.ListView,
):
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


class DetailView(InlineActionMixin, ComponentMixin, InlinesMixin, generic.DetailView):
    def get_template_names(self):
        return super().get_template_names() + ["beam/detail.html"]


class DeleteView(ComponentMixin, InlinesMixin, generic.DeleteView):
    def get_template_names(self):
        return super().get_template_names() + ["beam/delete.html"]

    def get_success_url(self):
        return self.viewset.links["list"].reverse(request=self.request)

    def get_success_message(self):
        return _('The {model} "{name}" was deleted successfully.').format(
            model=self.model._meta.verbose_name, name=str(self.object)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        nested, protected = self.get_nested_objects(self.object)
        if protected:
            return HttpResponseForbidden()

        success_message = self.get_success_message()

        response = self.delete(request, *args, **kwargs)

        if success_message:
            messages.success(request, success_message)

        return response

    @classmethod
    def get_nested_objects(cls, obj):
        using = router.db_for_write(cls.model)
        collector = NestedObjects(using=using)
        collector.collect([obj])
        nested = collector.nested(cls._format_obj)
        return nested, list(map(cls._format_obj, collector.protected))

    @staticmethod
    def _format_obj(obj):
        return '%s "%s"' % (obj._meta.verbose_name, str(obj))

    def get_context_data(self, **kwargs):
        context = super(DeleteView, self).get_context_data(**kwargs)
        nested, protected = self.get_nested_objects(self.get_object())
        context.update(
            {
                "object": self.object,
                "object_name": self._format_obj(self.object),
                "nested_objects": nested,
                "protected_objects": protected,
            }
        )
        return context


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
            viewsets = []
            for viewset in viewsets_dict.values():
                links = []
                for name in "list", "create":
                    link = viewset().links.get(name)
                    if link and link.has_perm(
                        user=self.request.user, obj=None, request=self.request
                    ):
                        links.append(link)

                if links:
                    viewsets.append((viewset, links))

            if not viewsets:
                continue

            group = {
                "app_label": app_label,
                "app_config": apps.get_app_config(app_label),
                "viewsets": viewsets,
            }
            grouped.append(group)
        context["grouped_by_app"] = grouped
        return context

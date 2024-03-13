import inspect
from typing import List, Mapping, Optional, Set, Type

import django_filters
from django.urls import reverse

from .actions import Action
from .utils import check_permission


class BaseComponent:
    show_link = True

    def __init__(
        self,
        viewset=None,
        name=None,
        verbose_name=None,
        url_name=None,
        url_kwargs=None,
        url_namespace=None,
        permission=None,
        resolve_url=None,
        **kwargs
    ):
        if not name:
            raise ValueError("Components need a name")

        self.viewset = viewset
        self.name = name
        self.verbose_name = verbose_name or self.name
        self.url_name = url_name
        self.url_kwargs = url_kwargs or {}
        self.resolve_url = resolve_url or reverse
        self.url_namespace = url_namespace

        if isinstance(permission, str):
            context = {"component": self}
            if getattr(self, "model", None) is not None:
                opts = self.model._meta
                context["model_name"] = opts.model_name
                context["app_label"] = opts.app_label
            self.permission = permission.format(**context)
        else:
            self.permission = permission

    def __repr__(self):
        if self.viewset:
            return "<{} {}.{} {}>".format(
                self.__class__.__name__,
                self.viewset.__module__,
                self.viewset.__class__.__name__,
                repr(self.name),
            )
        return "<{} {}>".format(self.__class__.__name__, repr(self.name))

    @classmethod
    def get_arguments(cls) -> Set[str]:
        """
        Get a list of arguments that can be passed from the viewset.

        These arguments will be used by ViewSet._get_components
        when instantiating components.
        """
        arguments = set()
        for class_ in inspect.getmro(cls):
            for arg in inspect.getfullargspec(class_).args[1:]:
                arguments.add(arg)
        return arguments

    def has_perm(self, user, obj=None, request=None, override_kwargs=None) -> bool:
        """
        Check whether a given user has access to this component.
        The optional parameters mirror those for reverse so that
        every possible url can be checked as well.

        :param obj: An optional model instance
        :param request: An optional request
        :param override_kwargs: An optional dict overriding url kwargs

        :return: A boolean, is the user allowed to interact with this component?
        """
        return check_permission(permission=self.permission, user=user, obj=obj)

    def reverse(self, obj=None, request=None, override_kwargs=None):
        """
        Get a url for this component.

        :param obj: An optional model instance
        :param request: An optional request
        :param override_kwargs: An optional dict overriding url kwargs
        :return: A url
        """
        kwargs = self.resolve_url_kwargs(obj, request, override_kwargs)
        url_name = self.url_name
        if self.url_namespace:
            url_name = self.url_namespace + ":" + url_name

        return self.resolve_url(url_name, kwargs=kwargs)

    def resolve_url_kwargs(self, obj=None, request=None, override_kwargs=None):
        """
        Used to build the url kwargs that Component.reverse passed to django's reverse.

        Keys with None values are dropped from the result so you can't have urls
        with None in them.

        :param obj: An optional model instance
        :param request: An optional request
        :param override_kwargs: An optional dict overriding url kwargs
        :return: A dict of url kwargs that can be passed to django's reverse.
        """
        override_kwargs = override_kwargs or {}
        kwargs = {}
        assert self.url_kwargs is not None, str(self.__dict__)
        for kwarg, name_or_callable in self.url_kwargs.items():
            if callable(name_or_callable):
                kwargs[kwarg] = name_or_callable(obj, request)
            elif hasattr(obj, name_or_callable):
                kwargs[kwarg] = getattr(obj, name_or_callable)
        kwargs.update(override_kwargs)

        return {k: v for k, v in kwargs.items() if v is not None}


class Component(BaseComponent):
    def __init__(
        self,
        view_class=None,
        fields=None,
        url=None,
        layout=None,
        queryset=None,
        model=None,
        inline_classes=None,
        link_layout=None,
        name=None,
        url_name=None,
        url_namespace=None,
        **kwargs
    ):
        self.url = url

        if not view_class:
            raise ValueError(
                "A component requires a view class, if you do "
                "not want to serve a view use BaseComponent"
            )
        self.view_class = view_class

        self.inline_classes = inline_classes

        self.fields = fields  # FIXME do the layout / fields auto-create thing
        self.layout = layout

        if model is None and queryset is None:
            raise ValueError(
                "Component {} needs at least one of model, queryset".format(name)
            )
        elif model is not None and queryset is None:
            queryset = model._default_manager
        elif queryset is not None and model is None:
            model = queryset.model

        self.model = model
        self.queryset = queryset

        if not url_name:
            url_name = "{}_{}_{}".format(
                self.model._meta.app_label, self.model._meta.model_name, name
            )

        self.link_layout = (
            link_layout if link_layout is not None else ["!{}".format(name), "..."]
        )
        super().__init__(
            name=name, url_name=url_name, url_namespace=url_namespace, **kwargs
        )

    @property
    def queryset(self):
        # ensure we don't keep stale copies of querysets
        return self._queryset.all()

    @queryset.setter
    def queryset(self, queryset):
        self._queryset = queryset


class FormComponent(Component):
    def __init__(self, form_class=None, **kwargs):
        self.form_class = form_class
        super().__init__(**kwargs)


class ListComponent(Component):
    def __init__(
        self,
        list_search_fields: Optional[List[str]] = None,
        list_paginate_by: Optional[int] = None,
        list_item_link_layout: Optional[List[str]] = None,
        list_sort_fields: Optional[List[str]] = None,
        list_sort_fields_columns: Optional[Mapping[str, str]] = None,
        list_filterset_fields: Optional[List[str]] = None,
        list_filterset_class: Optional[
            Type[django_filters.filterset.BaseFilterSet]
        ] = None,
        list_action_classes: Optional[List[Type[Action]]] = None,
        **kwargs
    ):
        self.list_search_fields = list_search_fields
        self.list_paginate_by = list_paginate_by
        self.list_item_link_layout = list_item_link_layout
        self.list_sort_fields = list_sort_fields
        self.list_sort_fields_columns = list_sort_fields_columns
        self.list_filterset_fields = list_filterset_fields
        self.list_filterset_class = list_filterset_class
        self.list_actions_classes = list_action_classes
        super().__init__(**kwargs)


class Link(BaseComponent):
    """
    A component class that can be added to ViewSet.links to add links to external views.

    Example usage:

        class SomeViewSet(beam.ViewSet):
            @property
            def links(self) -> Dict[str, BaseComponent]:
                links = super().links
                links["frontend"] = Link(
                    viewset=self,
                    name="frontend",
                    verbose_name=_("frontend"),
                    url_name="uploads_upload_frontend",
                    url_kwargs={"public_id": "public_id"},
                    permission="uploads.view_frontend",
                )
                return links
    """

    pass

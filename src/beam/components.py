import inspect
from typing import Set, TypeVar

from django.urls import reverse


class BaseComponent:
    show_link = True

    def __init__(
        self,
        name=None,
        verbose_name=None,
        url_name=None,
        url_kwargs=None,
        permission=None,
        **kwargs
    ):
        if not name:
            raise ValueError("Components need a name")

        self.name = name
        self.verbose_name = verbose_name or self.name
        self.url_name = url_name
        self.url_kwargs = url_kwargs

        if isinstance(permission, str):
            context = {"component": self}
            if getattr(self, "model", None) is not None:
                opts = self.model._meta
                context["model_name"] = opts.model_name
                context["app_label"] = opts.app_label
            self.permission = permission.format(**context)
        else:
            self.permission = permission

    @classmethod
    def get_arguments(cls) -> Set[str]:
        """
        Get a list of arguments that can be passed from the viewset.
        """
        arguments = set()
        for class_ in inspect.getmro(cls):
            for arg in inspect.getfullargspec(class_).args[1:]:
                arguments.add(arg)
        return arguments

    def get_context(self):
        return {name: getattr(self, name) for name in self.get_arguments()}

    def has_perm(self, user, obj=None):
        if self.permission is None:
            return True
        if not user:
            return False
        if callable(self.permission):
            return self.permission(user, obj=obj)
        # the ModelBackend returns False as soon as we supply an obj so we can't pass that here
        return user.has_perm(self.permission)

    def reverse(self, obj=None, extra_kwargs=None):
        if not obj:
            return reverse(self.url_name)

        if not obj and self.url_kwargs:
            return

        kwargs = {kwarg: getattr(obj, kwarg) for kwarg in self.url_kwargs}
        if extra_kwargs:
            kwargs.update(extra_kwargs)

        return reverse(self.url_name, kwargs=kwargs)


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
        **kwargs
    ):
        self.url = url

        if not view_class:
            raise ValueError(
                "A component requires a view class, if you do not want to serve a view use BaseComponent"
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
        self.queryset = queryset.all()  # ensure we don't keep stale copies of querysets

        if not url_name:
            url_name = "{}_{}_{}".format(
                self.model._meta.app_label, self.model._meta.model_name, name
            )

        self.link_layout = (
            link_layout if link_layout is not None else ["!{}".format(name), "..."]
        )
        super().__init__(name=name, url_name=url_name, **kwargs)


class FormComponent(Component):
    def __init__(self, form_class=None, **kwargs):
        self.form_class = form_class
        super().__init__(**kwargs)


class ListComponent(Component):
    def __init__(
        self,
        list_search_fields=None,
        list_paginate_by=None,
        list_item_link_layout=None,
        list_sort_fields=None,
        list_sort_fields_columns=None,
        **kwargs
    ):
        self.list_search_fields = list_search_fields
        self.list_paginate_by = list_paginate_by
        self.list_item_link_layout = list_item_link_layout
        self.list_sort_fields = list_sort_fields
        self.list_sort_fields_columns = list_sort_fields_columns
        super().__init__(**kwargs)


class Link(BaseComponent):
    """
    A component class that can be added to ViewSet.links to add links to external views.
    """

    show_link = True

    def __init__(
        self,
        name=None,
        verbose_name=None,
        url_name=None,
        url_kwargs=None,
        permission=None,
        **kwargs
    ):
        self.resolve_url = kwargs.pop("resolve_url", reverse)
        super().__init__(name, verbose_name, url_name, url_kwargs, permission, **kwargs)

    def reverse(self, obj=None, extra_kwargs=None):
        if not obj:
            return self.resolve_url(self.url_name)

        if not obj and self.url_kwargs:
            return

        kwargs = {kwarg: getattr(obj, kwarg) for kwarg in self.url_kwargs}
        if extra_kwargs:
            kwargs.update(extra_kwargs)

        return self.resolve_url(self.url_name, kwargs=kwargs)

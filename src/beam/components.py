import inspect
from typing import Set

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
        self.permission = permission  # FIXME string / list / callable
        self.url_name = url_name
        self.url_kwargs = url_kwargs

    @classmethod
    def get_arguments(cls) -> Set[str]:
        """
        Get a list of arguments that can be passed from the viewset.
        """
        arguments = set()
        for class_ in inspect.getmro(cls):
            for arg in inspect.getfullargspec(class_.__init__).args[1:]:
                arguments.add(arg)
        return arguments

    def get_context(self):
        return {name: getattr(self, name) for name in self.get_arguments()}

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
        **kwargs
    ):
        super().__init__(**kwargs)
        self.url = url

        if not view_class:
            raise ValueError(
                "A component requires a view class, if you do not want to serve a view use BaseComponent"
            )
        self.view_class = view_class

        self.inline_classes = inline_classes

        self.fields = fields  # FIXME do the layout / fields auto-create thing
        self.layout = layout

        if not model and not queryset:
            raise ValueError(
                "Component {} needs at least one of model, queryset".format(self.name)
            )
        elif model and not queryset:
            queryset = model._default_manager.all()
        elif queryset and not model:
            model = queryset.model

        self.model = model
        self.queryset = queryset

        if not self.url_name:
            self.url_name = "{}_{}_{}".format(
                self.model._meta.app_label, self.model._meta.model_name, self.name
            )

        self.link_layout = (
            link_layout if link_layout is not None else ["!{}".format(self.name), "..."]
        )


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
        **kwargs
    ):
        self.list_search_fields = list_search_fields
        self.list_paginate_by = list_paginate_by
        self.list_item_link_layout = list_item_link_layout
        super().__init__(**kwargs)

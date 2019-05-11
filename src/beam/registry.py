from collections import OrderedDict
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .viewsets import BaseViewSet
else:
    BaseViewSet = type


RegistryType = Dict[str, Dict[str, BaseViewSet]]


def register(registry: RegistryType, viewset: BaseViewSet):
    model = viewset.model
    app_label = model._meta.app_label
    model_name = model._meta.model_name

    app_registry = registry.setdefault(app_label, {})
    if model_name in app_registry:
        raise Exception(
            "Duplicate registration of {} for app label {} with model {}, "
            "beam.viewsets.unregister the existing viewset first.".format(
                viewset, app_label, registry
            )
        )
    app_registry[model_name] = viewset


def unregister(registry, model):
    app_label = model._meta.app_label
    model_name = model._meta.model_name

    if app_label not in registry:
        return

    app_registry = registry[app_label]

    if model_name not in app_registry:
        return

    app_registry.pop(model_name)

    if not app_registry:
        registry.pop(app_label)


def get_viewset_for_model(registry, model):
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    return registry[app_label][model_name]


class ViewsetMetaClass(type):
    def __new__(mcs, name, bases, attrs):
        # Collect components from current class.
        current_component_classes = []
        for key, value in list(attrs.items()):
            if key.endswith("_component"):
                current_component_classes.append((key[: -len("_component")], value))
        attrs["_declared_component_classes"] = OrderedDict(current_component_classes)

        new_class: BaseViewSet = super().__new__(mcs, name, bases, attrs)

        # Walk through the MRO.
        declared_component_classes = OrderedDict()
        for base in reversed(new_class.__mro__):
            # Collect fields from base class.
            if hasattr(base, "_declared_component_classes"):
                declared_component_classes.update(base._declared_component_classes)

            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_component_classes:
                    declared_component_classes.pop(attr)

        new_class._component_classes = list(declared_component_classes.items())
        new_class._declared_component_classes = declared_component_classes

        if (
            new_class.registry is not None
            and getattr(new_class, "model", None) is not None
        ):
            register(new_class.registry, new_class)

        return new_class


default_registry: RegistryType = {}

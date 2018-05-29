def register(registry, model, viewset):
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


class RegistryMetaClass(type):

    def __new__(cls, name, bases, namespace, **kwds):
        result = type.__new__(cls, name, bases, dict(namespace))

        if result.registry is not None and result.model is not None:
            register(result.registry, result.model, result)

        return result


default_registry = {}

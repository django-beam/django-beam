from django import template
from django.apps import apps
from django.db.models import Model, QuerySet, Manager
from django.db.models.fields.files import ImageFieldFile, FieldFile
from django.template.loader import get_template
from django.urls import NoReverseMatch

from beam.registry import default_registry, get_viewset_for_model

register = template.Library()


@register.simple_tag
def get_link_url(link, obj=None):
    try:
        return link.get_url(obj)
    except NoReverseMatch:
        return None


@register.simple_tag
def get_attribute(obj, field_name):
    if not hasattr(obj, field_name):
        return None
    if hasattr(obj, "get_{}_display".format(field_name)):
        return getattr(obj, "get_{}_display".format(field_name))
    value = getattr(obj, field_name)

    if isinstance(value, Manager):
        return value.all()

    return value


@register.filter
def is_queryset(value):
    return isinstance(value, QuerySet)


@register.simple_tag(takes_context=True)
def get_url_for_related(context, instance, view_type):
    opts = get_options(instance)

    viewset = context.get("viewset", None)
    if viewset:
        registry = viewset.registry
    else:
        registry = default_registry

    try:
        viewset = get_viewset_for_model(registry, opts.model)
    except KeyError:
        return None

    return viewset().links[view_type].get_url(instance)


@register.filter
def is_image(model_field):
    return isinstance(model_field, ImageFieldFile)


@register.filter
def is_file(model_field):
    return isinstance(model_field, FieldFile)


@register.simple_tag
def get_options(instance_or_model):
    """
    Return the _meta options for a given model or instance.
    """
    if not instance_or_model:
        return None

    if isinstance(instance_or_model, Model):
        model = instance_or_model.__class__
    else:
        model = instance_or_model

    return model._meta


@register.filter
def field_verbose_name(instance, field_name):
    options = get_options(instance)
    field = options.get_field(field_name)

    return getattr(field, "verbose_name", field_name.replace("_", ""))


@register.simple_tag(takes_context=True)
def render_navigation(context):
    grouped = []
    for app_label, viewsets_dict in default_registry.items():
        group = {
            "app_label": app_label,
            "app_config": apps.get_app_config(app_label),
            "viewsets": viewsets_dict.values(),
        }
        grouped.append(group)
    navigation_template = get_template("beam/navigation.html")
    request = context.get("request", None)
    return navigation_template.render({"apps": grouped, "request": request})

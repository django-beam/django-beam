from django import template
from django.apps import apps
from django.db.models import Model
from django.db.models.fields.files import ImageFieldFile, FieldFile
from django.template.loader import get_template
from django.urls import NoReverseMatch

from beam.registry import default_registry

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
    return getattr(obj, field_name)


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

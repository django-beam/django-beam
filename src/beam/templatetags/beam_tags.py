from django import template
from django.db.models.fields.files import ImageFieldFile, FieldFile
from django.urls import NoReverseMatch

register = template.Library()


@register.simple_tag
def get_link_url(link, obj=None):
    try:
        return link.get_url(obj)
    except NoReverseMatch:
        return None


@register.simple_tag
def get_field(obj, field_name):
    if not hasattr(obj, field_name):
        return None
    if hasattr(obj, 'get_{}_display'.format(field_name)):
        return getattr(obj, 'get_{}_display'.format(field_name))
    return getattr(obj, field_name)


@register.filter
def is_image(model_field):
    return isinstance(model_field, ImageFieldFile)


@register.filter
def is_file(model_field):
    return isinstance(model_field, FieldFile)
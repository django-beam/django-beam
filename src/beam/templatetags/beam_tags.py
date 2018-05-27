from django import template
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
    return getattr(obj, field_name)

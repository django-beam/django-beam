import inspect
from django import template


register = template.Library()


@register.simple_tag
def resolve_link(link_resolver, obj=None):
    return link_resolver(obj)


@register.simple_tag
def get_field(obj, field_name):
    if not hasattr(obj, field_name):
        return None
    return getattr(obj, field_name)
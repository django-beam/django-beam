import inspect
from collections import OrderedDict
from django import template


register = template.Library()


@register.simple_tag
def resolve_links(links, obj=None):
    resolved = []
    for view_type, resolver in links:
        if "obj" not in inspect.signature(resolver).parameters:
            resolved.append((view_type, resolver()))
        elif obj is not None:
            resolved.append((view_type, resolver(obj)))
    return OrderedDict(resolved)


@register.simple_tag
def get_field(obj, field_name):
    if not hasattr(obj, field_name):
        return None
    return getattr(obj, field_name)

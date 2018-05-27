import inspect


def resolve_link(link_resolver, obj=None):
    if 'obj' not in inspect.signature(link_resolver).parameters:
        return link_resolver()
    if obj is None:
        return None
    return link_resolver(obj)

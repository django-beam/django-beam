from typing import Optional, Tuple

from django.urls import NoReverseMatch


def check_permission(permission, user, obj):
    if permission is None:
        return True
    if not user:
        return False
    if callable(permission):
        return permission(user, obj=obj)
    # the ModelBackend returns False as soon as we supply an obj so we can't pass that here
    return user.has_perm(permission)


def navigation_component_entry(
    component=None, user=None, request=None
) -> Optional[Tuple[str, str]]:
    """
    Get an optional tuple (label, url) for a given compoment to use in render_navigation
    """
    if not component:
        return None

    if not component.has_perm(user=user, obj=None, request=request):
        return None

    try:
        url = component.reverse(obj=None, request=request)
    except NoReverseMatch:
        return None

    model = getattr(component, "model", None)
    if model and component.name == "list":
        label = model._meta.verbose_name_plural
    else:
        label = component.verbose_name

    return label, url


def reverse_component(component, obj, request, override_kwargs):
    """
    Reverse a component and raise helpful error messages if reversing fails.
    """
    try:
        return component.reverse(
            obj=obj, request=request, override_kwargs=override_kwargs
        )
    except NoReverseMatch as e:
        raise NoReverseMatch(f"Unable to reverse url to {component}: {e}") from e
    except BaseException as e:
        raise Exception(f"Unable to reverse url to {component}: {e}") from e

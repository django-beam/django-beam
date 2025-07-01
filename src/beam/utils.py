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


def navigation_facet_entry(
    facet=None, user=None, request=None
) -> Optional[Tuple[str, str]]:
    """
    Get an optional tuple (label, url) for a given facet to use in render_navigation
    """
    if not facet:
        return None

    if not facet.has_perm(user=user, obj=None, request=request):
        return None

    try:
        url = facet.reverse(obj=None, request=request)
    except NoReverseMatch:
        return None

    model = getattr(facet, "model", None)
    if model and facet.name == "list":
        label = model._meta.verbose_name_plural
    else:
        label = facet.verbose_name

    return label, url


def reverse_facet(facet, obj, request, override_kwargs):
    """
    Reverse a facet and raise helpful error messages if reversing fails.
    """
    try:
        return facet.reverse(obj=obj, request=request, override_kwargs=override_kwargs)
    except NoReverseMatch as e:
        raise NoReverseMatch(f"Unable to reverse url to {facet}: {e}") from e
    except BaseException as e:
        raise Exception(f"Unable to reverse url to {facet}: {e}") from e

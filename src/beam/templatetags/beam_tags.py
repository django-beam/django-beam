import decimal
from typing import Dict, List, Sequence, Tuple
from urllib.parse import ParseResult, parse_qsl, urlparse

from django import template
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Manager, Model, QuerySet
from django.db.models.fields.files import FieldFile, ImageFieldFile
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.forms import Form
from django.template import RequestContext
from django.template.loader import get_template
from django.utils.html import escape
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from beam.facets import BaseFacet
from beam.layouts import layout_links
from beam.registry import default_registry, get_viewset_for_model
from beam.utils import navigation_facet_entry, reverse_facet

register = template.Library()


@register.simple_tag(takes_context=True)
def get_link_url(
    context: RequestContext, facet: BaseFacet, obj=None, **override_kwargs
):
    request = getattr(context, "request", None)
    if not facet:
        return None

    return reverse_facet(
        facet, obj=obj, request=request, override_kwargs=override_kwargs
    )


@register.simple_tag
def get_attribute(obj, field):
    if getattr(field, "is_virtual", False):
        return field.get_value(obj)

    if not hasattr(obj, field):
        return None

    if hasattr(obj, "get_{}_display".format(field)):
        return getattr(obj, "get_{}_display".format(field))

    value = getattr(obj, field)

    if isinstance(value, Manager):
        return value.all()

    return value


@register.simple_tag
def get_form_field(form, field):
    try:
        return form[field]
    except KeyError:
        return None


@register.filter
def is_queryset(value):
    return isinstance(value, QuerySet)


@register.simple_tag(takes_context=True)
def get_url_for_related(context, instance, facet_name, **override_kwargs):
    if not instance:
        return None

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

    facets = viewset().facets
    if facet_name not in facets:
        return None

    request = getattr(context, "request", None)

    facet = facets[facet_name]

    if request and not facet.has_perm(
        request.user, obj=instance, request=request, override_kwargs=override_kwargs
    ):
        return None

    return reverse_facet(
        facet=facet,
        obj=instance,
        request=request,
        override_kwargs=override_kwargs,
    )


@register.filter
def is_image(value):
    return isinstance(value, ImageFieldFile)


@register.filter
def is_file(value):
    return isinstance(value, FieldFile)


@register.filter
def is_bool(value):
    return isinstance(value, bool)


@register.filter
def is_int(value):
    return isinstance(value, int)


@register.filter
def is_float(value):
    return isinstance(value, float)


@register.filter
def is_decimal(value):
    return isinstance(value, decimal.Decimal)


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
def field_verbose_name(instance, field):
    if hasattr(field, "verbose_name"):
        return field.verbose_name

    options = get_options(instance)

    try:
        model_field = options.get_field(field)
    except FieldDoesNotExist:
        model_field = None

    if hasattr(model_field, "verbose_name"):
        return model_field.verbose_name

    if isinstance(model_field, ForeignObjectRel):
        if model_field.multiple:
            return model_field.related_model._meta.verbose_name_plural
        else:
            return model_field.related_model._meta.verbose_name

    value = getattr(instance, field, None)
    return getattr(value, "verbose_name", field.replace("_", " "))


@register.filter(name="any")
def any_filter(iterable):
    if not iterable:
        return False
    return any(iterable)


@register.simple_tag(takes_context=True)
def get_apps_for_navigation(context):
    request = context.get("request", None)
    user = request.user if request else None

    apps_with_entries = []
    for app_label, viewsets_dict in default_registry.items():
        entries = []
        for viewset in viewsets_dict.values():
            entry = navigation_facet_entry(
                viewset().links.get("list"), user=user, request=request
            )
            if entry:
                entries.append(entry)

        if not entries:
            continue

        group = {
            "app_label": app_label,
            "app_config": apps.get_app_config(app_label),
            "entries": entries,
        }
        apps_with_entries.append(group)
    return apps_with_entries


@register.simple_tag(takes_context=True)
def render_navigation(context):
    """
    Render the navigation template with the apps.

    Deprecated: use get_apps_for_navigation instead.
    """
    apps = get_apps_for_navigation(context)
    request = context.get("request", None)
    navigation_template = get_template("beam/partials/navigation.html")
    return navigation_template.render({"apps": apps, "request": request})


@register.simple_tag()
def fields_to_layout(fields):
    return [[fields]]


@register.simple_tag(takes_context=True)
def sort_link(context, field: str, sorted_fields: Sequence[str], page_param=None):
    sort_param = context["view"].sort_param
    sort_separator = context["view"].sort_separator

    sorted_fields = list(sorted_fields)
    negated_field = "-" + field

    if field in sorted_fields:
        sorted_fields.remove(field)
        sorted_fields.append(negated_field)
    elif negated_field in sorted_fields:
        sorted_fields.remove(negated_field)
        sorted_fields.append(field)
    else:
        sorted_fields.append(field)

    return preserve_query_string(
        context,
        ignore_params=page_param,
        **{sort_param: sort_separator.join(sorted_fields)},
    )


@register.simple_tag(takes_context=True)
def page_link(context, page_param, page_number):
    return preserve_query_string(context, **{page_param: page_number})


@register.simple_tag(takes_context=True)
def preserve_query_string(context, ignore_params=None, **kwargs):
    get = preserve_get_params(context, ignore_params=ignore_params, **kwargs)
    return "?{}".format(get.urlencode())


@register.simple_tag(takes_context=True)
def preserve_get_params_as_hidden_inputs(context, ignore_params=None, **kwargs):
    get = preserve_get_params(context, ignore_params=ignore_params, **kwargs)
    inputs = [
        f'<input type="hidden" name="{escape(k)}" value="{escape(v)}">'
        for k, v in get.items()
    ]
    return mark_safe("".join(inputs))


@register.simple_tag(takes_context=True)
def preserve_get_params(context, ignore_params=None, **kwargs):
    """Preserve GET parameters from the current URL, whilst overwriting parameters
    given by optional kwargs. Optional ignore_params will be removed from the parameters.

    :param context: a Django template context
    :param ignore_params: if provided, the ignore_params will be removed from the get parameters
    :param kwargs: further kwargs will overwrite parameters with the given values
    :return: a dict with all preserved get parameters
    """
    if "request" not in context:
        raise Exception(
            "The preserve_get_params tag requires django.core.context_processors.request"
        )

    request = context["request"]
    get = request.GET.copy()

    # ignore_params may be a string
    if isinstance(ignore_params, str):
        get.pop(ignore_params, None)

    # or a list of strings
    elif isinstance(ignore_params, list):
        for param in ignore_params:
            get.pop(param, None)

    # kwargs overwrite the parameters
    for key, value in kwargs.items():
        if value == "":
            get.pop(key, None)
        else:
            get[key] = value

    return get


@register.simple_tag
def build_ignore_params(*args):
    """
    Builds a list of parameter names which should be ignored when preserving GET params.

    :param args: each arg may be a name of a parameter to ignore
        or a form, whose fields should be ignored
    :return: a list of parameter names to ignore
    """
    ignore_params = []
    for arg in args:
        if isinstance(arg, Form):
            for field in arg:
                key = field.name
                if arg.prefix:
                    key = arg.prefix + "-" + key
                ignore_params.append(key)
        elif isinstance(arg, str):
            ignore_params.append(arg)

    return ignore_params


def _add_params_to_url_if_new(url, default_params):
    """
    Add params from default_params unless they already exist.
    """
    parsed_url = urlparse(url)
    existing_params = parse_qsl(parsed_url.query)

    params = {}
    params.update(default_params)
    params.update(existing_params)

    return ParseResult(
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        urlencode(params),
        parsed_url.fragment,
    ).geturl()


PRESERVED_GET_PARAMS = [
    "_popup",
]  # get parameters that should be preserved while following links


@register.simple_tag(takes_context=True)
def get_visible_links(
    context: RequestContext,
    user,
    links: Dict[str, BaseFacet],
    link_layout: List[str],
    obj: Model = None,
    **override_kwargs,
) -> List[Tuple[BaseFacet, str]]:

    get_params = {}
    request = getattr(context, "request", None)
    if request:
        for param in PRESERVED_GET_PARAMS:
            value = request.GET.get(param)
            if value:
                get_params[param] = value

    visible_links = []
    for facet in layout_links(links, link_layout):
        if not facet.has_perm(
            user, obj=obj, request=request, override_kwargs=override_kwargs
        ):
            continue

        url = reverse_facet(
            facet=facet,
            obj=obj,
            request=request,
            override_kwargs=override_kwargs,
        )

        if url and get_params:
            url = _add_params_to_url_if_new(url, get_params)

        if url:
            visible_links.append((facet, url))
    return visible_links

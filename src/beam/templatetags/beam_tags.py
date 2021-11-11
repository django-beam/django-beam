from typing import Dict, List, Sequence, Tuple
from urllib.parse import ParseResult, parse_qsl, urlparse

from beam.components import BaseComponent
from beam.layouts import layout_links
from beam.registry import default_registry, get_viewset_for_model
from beam.utils import navigation_component_entry
from django import template
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Manager, Model, QuerySet
from django.db.models.fields.files import FieldFile, ImageFieldFile
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.template import RequestContext
from django.template.loader import get_template
from django.urls import NoReverseMatch
from django.utils.http import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def get_link_url(
    context: RequestContext, component: BaseComponent, obj=None, **override_kwargs
):
    request = getattr(context, "request", None)
    if not component:
        return None
    try:
        return component.reverse(
            obj=obj, request=request, override_kwargs=override_kwargs
        )
    except NoReverseMatch:
        return None


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
def get_url_for_related(context, instance, component_name, **override_kwargs):
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

    components = viewset().components
    if component_name not in components:
        return None

    request = getattr(context, "request", None)

    component = components[component_name]

    if request and not component.has_perm(
        request.user, obj=instance, request=request, override_kwargs=override_kwargs
    ):
        return None

    try:
        return component.reverse(instance, request, override_kwargs)
    except NoReverseMatch:
        return None


@register.filter
def is_image(model_field):
    return isinstance(model_field, ImageFieldFile)


@register.filter
def is_file(model_field):
    return isinstance(model_field, FieldFile)


@register.filter
def is_bool(model_field):
    return isinstance(model_field, bool)


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
def render_navigation(context):
    request = context.get("request", None)
    user = request.user if request else None

    grouped = []
    for app_label, viewsets_dict in default_registry.items():
        entries = []
        for viewset in viewsets_dict.values():
            entry = navigation_component_entry(
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
        grouped.append(group)
    navigation_template = get_template("beam/partials/navigation.html")
    request = context.get("request", None)
    return navigation_template.render({"apps": grouped, "request": request})


@register.simple_tag()
def fields_to_layout(fields):
    return [[fields]]


@register.simple_tag(takes_context=True)
def sort_link(context, field: str, sorted_fields: Sequence[str]):
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
        context, **{"page": "", sort_param: sort_separator.join(sorted_fields)}
    )


@register.simple_tag(takes_context=True)
def page_link(context, page_query_string, page_number):
    return preserve_query_string(context, **{page_query_string: page_number})


@register.simple_tag(takes_context=True)
def preserve_query_string(context, **kwargs):
    if "request" not in context:
        raise Exception(
            "The query_string tag requires django.core.context_processors.request"
        )
    request = context["request"]

    get = request.GET.copy()

    for item, value in kwargs.items():
        if value == "":
            get.pop(item, None)
        else:
            get[item] = value

    return "?{}".format(get.urlencode())


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
    links: Dict[str, BaseComponent],
    link_layout: List[str],
    obj: Model = None,
    **override_kwargs
) -> List[Tuple[BaseComponent, str]]:

    get_params = {}
    request = getattr(context, "request", None)
    if request:
        for param in PRESERVED_GET_PARAMS:
            value = request.GET.get(param)
            if value:
                get_params[param] = value

    visible_links = []
    for link in layout_links(links, link_layout):
        if not link.has_perm(
            user, obj=obj, request=request, override_kwargs=override_kwargs
        ):
            continue
        try:
            url = link.reverse(obj, request=request, override_kwargs=override_kwargs)
        except NoReverseMatch:
            url = None

        if url and get_params:
            url = _add_params_to_url_if_new(url, get_params)

        if url:
            visible_links.append((link, url))
    return visible_links

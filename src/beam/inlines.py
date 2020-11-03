from typing import List, Optional, Type

from beam.actions import Action
from django.core.paginator import Page, Paginator
from django.db.models import Model
from django.db.models.options import Options
from django.forms import ModelForm, inlineformset_factory
from django_filters.filterset import filterset_factory


class BaseRelatedInline(object):
    model: Model
    title: str = ""
    foreign_key_field: str
    layout = None
    fields: List[str] = []
    extra = None
    can_delete = True
    can_order = False
    order_field: str = ""
    queryset = None
    form_class = ModelForm

    def __init__(self, parent_instance=None, parent_model=None, request=None) -> None:
        super().__init__()
        self.parent_instance = parent_instance
        self.parent_model = parent_model
        self.request = request
        self._formset = None
        self.prefix = self.get_prefix()
        assert self.foreign_key_field, "you must set a foreign key field"
        assert (
            not self.can_order or self.order_field
        ), "you must set order_field when using can_order=True"

    @property
    def formset(self):
        if self._formset is None:
            self._formset = self.construct_formset()
        return self._formset

    def get_prefix(self):
        # FIXME would rather have a unique prefix!
        # same implementation as default InlineFormset
        return (
            self.model_options.get_field(self.foreign_key_field)
            .remote_field.get_accessor_name(model=self.model)
            .replace("+", "")
        )

    def get_formset_class(self):
        if self.extra is not None:
            extra = self.extra
        elif self.parent_instance:
            extra = 0
        else:
            extra = 1

        return inlineformset_factory(
            parent_model=self.parent_model,
            form=self.form_class,
            model=self.model,
            fk_name=self.foreign_key_field,
            extra=extra,
            can_delete=self.can_delete,
            fields=self.fields[:],
        )

    def get_formset_kwargs(self):
        return {
            "instance": self.parent_instance,
            "data": self.request.POST if self.request and self.request.POST else None,
            "files": self.request.FILES
            if self.request and self.request.FILES
            else None,
            "prefix": self.prefix,
        }

    def construct_formset(self):
        formset_class = self.get_formset_class()
        return formset_class(**self.get_formset_kwargs())

    def get_title(self):
        return self.title or self.model_options.verbose_name_plural

    def get_queryset(self):
        if self.queryset:
            # ensure re-evaluation of queryset
            qs = self.queryset.all()
        else:
            qs = self._get_queryset_from_parent_instance()

        if not qs.ordered:
            # ensure a stable order
            qs = qs.order_by("pk")

        return qs

    def _get_queryset_from_parent_instance(self):
        if self.parent_instance is None:
            return self.model.objects.none()
        related_name = self.model_options.get_field(
            self.foreign_key_field
        ).remote_field.get_accessor_name()
        return getattr(self.parent_instance, related_name).all()

    @property
    def model_options(self) -> Options:
        return self.model._meta


class NotPaginated(Page):
    """
    A single page that holds all objects.
    """

    def __init__(self, object_list, number, paginator):
        super().__init__(object_list, number, paginator)

        class NoPaginator:
            @property
            def count(self):
                return len(object_list)

        self.paginator = NoPaginator()

    def has_next(self):
        return False

    def has_previous(self):
        return False

    def start_index(self):
        return 1

    def end_index(self):
        return 1


class PaginationMixin(BaseRelatedInline):
    paginate_by: Optional[int] = None
    paginator_class = Paginator

    def __init__(self, parent_instance=None, parent_model=None, request=None) -> None:
        super().__init__(parent_instance, parent_model, request)
        assert not (
            self.paginate_by and self.can_order
        ), "ordering can't be enabled at the same time as pagination"

    @property
    def page_param(self):
        return "{}-page".format(self.prefix)

    @property
    def page(self) -> Page:
        queryset = self.get_queryset()
        if self.paginate_by:
            paginator = self.paginator_class(queryset, self.paginate_by)
            page_number = self.request.GET.get(self.page_param, 1)
            return paginator.page(page_number)
        else:
            return NotPaginated(object_list=queryset, number=1, paginator=None)

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        if self.paginate_by:
            queryset = self.get_queryset()
            # because pagination will slice the queryset and the formset will filter
            # it again which isn't possible so we create an unsliced one with just
            # the objects on the current page
            object_ids = (obj.pk for obj in self.page.object_list)
            kwargs["queryset"] = queryset.filter(pk__in=object_ids)
        return kwargs


class FilterSetMixin(BaseRelatedInline):
    filterset_class = None
    filterset_fields: Optional[List[str]] = None

    def __init__(self, parent_instance=None, parent_model=None, request=None) -> None:
        super().__init__(parent_instance, parent_model, request)
        self.filterset = self.get_filterset()

    def get_filterset_fields(self):
        return self.filterset_fields

    def get_filterset_class(self):
        if self.filterset_class:
            return self.filterset_class
        elif self.get_filterset_fields():
            return filterset_factory(
                model=self.model, fields=self.get_filterset_fields()
            )
        return None

    def get_filterset_kwargs(self):
        """
        Returns the keyword arguments for instantiating the filterset.
        """

        kwargs = {
            "data": self.request.GET or None,
            "request": self.request,
            # self.get_queryset() uses filterset to filter so must use super()
            "queryset": super().get_queryset(),
            "prefix": "{}-filter".format(self.prefix),
        }
        return kwargs

    def get_filterset(self):
        filterset_class = self.get_filterset_class()
        if not filterset_class:
            return None
        return filterset_class(**self.get_filterset_kwargs())

    def get_queryset(self):
        if self.filterset and self.filterset.is_bound and self.filterset.is_valid():
            return self.filterset.qs
        else:
            return super().get_queryset()


class ActionsMixin(BaseRelatedInline):
    action_classes: List[Type[Action]] = []

    def __init__(self, parent_instance=None, parent_model=None, request=None) -> None:
        super().__init__(parent_instance, parent_model, request)
        self.actions = self.get_actions()

    def get_action(self):
        for action in self.actions:
            if action.is_bound:
                return action
        return None

    def get_actions(self):
        if not self.action_classes:
            return []

        selected_action = self.request.POST.get("_action_choice")
        actions = []
        action_class: Type[Action]
        for index, action_class in enumerate(self.action_classes):
            action_id = "{}-{}-{}".format(self.prefix, index, action_class.name)
            action = action_class(
                data=self.request.POST if action_id == selected_action else None,
                model=self.model,
                id=action_id,
                request=self.request,
            )
            if action.has_perm(self.request.user):
                actions.append(action)
        return actions


class RelatedInline(ActionsMixin, FilterSetMixin, PaginationMixin, BaseRelatedInline):
    pass

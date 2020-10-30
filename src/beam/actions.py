from typing import Dict, List, Optional, Type

from django.db.models import Model, QuerySet
from django.forms import modelform_factory
from django.forms.forms import BaseForm
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from .utils import check_permission


class Action:
    name: str
    verbose_name: str
    permission: Optional[str] = None
    form_class: Optional[Type[BaseForm]] = None

    def __init__(
        self,
        data: Optional[Dict],
        model: Type[Model],
        id: str,
        request: Optional[HttpRequest],
    ):
        self.data = data
        self.is_bound = data is not None

        self.model = model
        self.id = id
        self.data = data
        self.request = request

        self._form: Optional[BaseForm] = None
        self._permission: Optional[str] = None

    def get_form(self):
        if self._form is None:
            form_class = self.get_form_class()
            if form_class is not None:
                self._form = form_class(data=self.data, prefix=self.id)
        return self._form

    def get_form_class(self) -> Optional[Type[BaseForm]]:
        return self.form_class

    def get_permission(self):
        if self._permission is None and self.permission is not None:
            if isinstance(self.permission, str) and self.model is not None:
                opts = self.model._meta
                self._permission = self.permission.format(
                    action=self, model_name=opts.model_name, app_label=opts.app_label
                )
            else:
                self._permission = self.permission
        return self._permission

    def has_perm(self, user, obj=None):
        # FIXME how should row level permissions be implemented?
        return check_permission(permission=self.get_permission(), user=user, obj=obj)

    def apply(self, queryset: QuerySet) -> Optional[HttpResponse]:
        """
        This applies the action to the queryset.
        Form validation and permission handling happens earlier
        :param queryset:

        :return:
        """
        raise NotImplementedError()

    def get_success_message(self):
        return ""


class DeleteAction(Action):
    name = "delete"
    verbose_name = gettext_lazy("delete")
    permission = "{app_label}.delete_{model_name}"

    def __init__(
        self,
        data: Optional[Dict],
        model: Type[Model],
        id: str,
        request: Optional[HttpRequest],
    ):
        super().__init__(data, model, id, request)
        self.count = 0

    def apply(self, queryset):
        self.count = queryset.delete()[0]

    def get_success_message(self):
        return _("Deleted {count} {name}").format(
            count=self.count, name=self.model._meta.verbose_name_plural,
        )


class MassUpdateAction(Action):
    name = "update_selected"
    verbose_name = gettext_lazy("update selected")
    permission = "{app_label}.change_{model_name}"

    form_fields: List[str] = []
    form_layout = None
    form_class = None

    def __init__(
        self,
        data: Optional[Dict],
        model: Type[Model],
        id: str,
        request: Optional[HttpRequest],
    ):
        super().__init__(data, model, id, request)
        self.changed = 0

    def get_form_class(self, **kwargs):
        return modelform_factory(model=self.model, fields=self.form_fields, **kwargs)

    def apply(self, queryset):
        form = self.get_form()
        if not form.is_valid():
            raise AssertionError(
                "Ensure that form validation is done before applying this action."
            )

        self.changed = 0
        for instance in queryset:
            instance_changed = False
            for field in form.changed_data:
                current_value = getattr(instance, field, None)
                new_value = form.cleaned_data[field]
                if current_value != new_value:
                    setattr(instance, field, new_value)
                    instance_changed = True
            if instance_changed:
                self.changed += 1
                instance.save()

    def get_success_message(self):
        return _("Updated {count} {name}").format(
            count=self.changed, name=self.model._meta.verbose_name_plural
        )

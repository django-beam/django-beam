from django.db.models import Model
from django.forms import inlineformset_factory, ModelForm
from typing import List


class RelatedInline(object):
    model: Model
    title: str = ""
    foreign_key_field: str
    layout = None
    fields: List[str] = []
    extra = None
    can_delete = True
    can_order = False
    order_field: str = ""

    form_class = ModelForm

    def __init__(self, parent_instance=None, parent_model=None, request=None) -> None:
        super().__init__()
        self.parent_instance = parent_instance
        self.parent_model = parent_model
        self.request = request
        self._formset = None
        assert self.foreign_key_field, "you must set a foreign key field"
        assert (
            not self.can_order or self.order_field
        ), "you must set order_field when using can_order=True"

    @property
    def formset(self):
        if self._formset is None:
            self._formset = self.construct_formset()
        return self._formset

    def construct_formset(self):
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
            fields=self.fields,
        )(
            instance=self.parent_instance,
            data=self.request.POST or None,
            files=self.request.FILES or None,
        )

    def get_title(self):
        return self.title or self.model._meta.verbose_name_plural

    @property
    def instances(self):
        related_name = self.model._meta.get_field(
            self.foreign_key_field
        ).remote_field.get_accessor_name()
        return getattr(self.parent_instance, related_name).all()

from django.forms import inlineformset_factory


class RelatedInline(object):
    model = None
    title = None
    foreign_key_field = None
    layout = None
    fields = []
    extra = 1
    can_delete = True

    def __init__(self, parent_instance=None, parent_model=None, request=None) -> None:
        super().__init__()
        self.parent_instance = parent_instance
        self.parent_model = parent_model
        self.request = request
        self._formset = None
        assert self.foreign_key_field, "you must set a foreign key field"

    @property
    def formset(self):
        if self._formset is None:
            self._formset = self.construct_formset()
        return self._formset

    def construct_formset(self):
        return inlineformset_factory(
            parent_model=self.parent_model,
            model=self.model,
            fk_name=self.foreign_key_field,
            extra=self.extra,
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

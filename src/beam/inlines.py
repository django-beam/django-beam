from django.forms import inlineformset_factory


class RelatedInline(object):
    model = None
    title = None
    foreign_key_field = None
    fields = []

    def __init__(self, parent_instance=None, parent_model=None, request=None) -> None:
        super().__init__()
        self.parent_instance = parent_instance
        self.parent_model = parent_model
        self.request = request
        self.formset = self.construct_formset()

    def construct_formset(self):
        return inlineformset_factory(
            parent_model=self.parent_model,
            model=self.model,
            fk_name=self.foreign_key_field,
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
        related_name = self.model._meta.get_field("car").remote_field.related_name
        return getattr(self.parent_instance, related_name).all()

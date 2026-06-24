from django.forms import SelectMultiple
from django.utils.translation import gettext_lazy as _


class DaisyUISelectMultiple(SelectMultiple):
    # FIXME we need something instead of bootstrap-select
    def __init__(self, attrs=None, choices=()):
        attrs = {} if attrs is None else attrs.copy()
        # this is config for bootstra-select
        attrs["class"] = "select select-bordered w-full"
        attrs["multiple"] = True
        attrs["data-live-search"] = "true"
        attrs["data-live-search-normalize"] = "true"
        attrs["data-selected-text-format"] = "count > 3"
        attrs["data-actions-box"] = "all"
        attrs["data-deselect-all-text"] = _("Deselect all")
        attrs["data-select-all-text"] = _("Select all")
        attrs["data-count-selected-text"] = _("{0} selected")
        attrs["data-none-selected-text"] = _("None selected")
        super().__init__(attrs, choices)

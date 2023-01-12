from django.forms import SelectMultiple
from django.utils.translation import gettext_lazy as _


class BootstrapSelectMultiple(SelectMultiple):
    def __init__(self, attrs=None, choices=()):
        attrs = {} if attrs is None else attrs.copy()
        attrs["class"] = "selectpicker"
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

    class Media:
        js = ["beam_contrib_auth/js/bootstrap-select.min.js"]
        css = {
            "all": ["beam_contrib_auth/css/bootstrap-select.min.css"],
        }

from django import template
from django.forms.widgets import CheckboxInput

register = template.Library()


@register.filter
def field_type(field):
    """
    Return the widget type of a form field.
    """
    if hasattr(field, "field"):
        widget = field.field.widget
        widget_class = widget.__class__.__name__.lower()

        # Map Django widget types to HTML input types
        if "checkbox" in widget_class:
            if "selectmultiple" in widget_class:
                return "checkboxselectmultiple"
            return "checkbox"
        elif "select" in widget_class:
            return "select"
        elif "textarea" in widget_class:
            return "textarea"
        elif "fileinput" in widget_class or "clearablefileinput" in widget_class:
            return "file"
        elif "numberinput" in widget_class:
            return "number"
        elif "emailinput" in widget_class:
            return "email"
        elif "urlinput" in widget_class:
            return "url"
        elif "passwordinput" in widget_class:
            return "password"
        elif "dateinput" in widget_class:
            return "date"
        elif "datetimeinput" in widget_class:
            return "datetime-local"
        elif "timeinput" in widget_class:
            return "time"
        elif "hiddeninput" in widget_class:
            return "hidden"
        else:
            return "text"
    return "text"


@register.filter
def is_checkbox(field):
    """
    Check if a form field is a checkbox.
    """
    if hasattr(field, "field"):
        return isinstance(field.field.widget, CheckboxInput)
    return False

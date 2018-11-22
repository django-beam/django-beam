from django.core.exceptions import ValidationError


def layout_contains_fields(layout, fields):
    # no layout is a valid layout, one will be generated
    if layout is None:
        return True

    layout_fields = {field for row in layout for col in row for field in col}

    return not (set(fields) - layout_fields)

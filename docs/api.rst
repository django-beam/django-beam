===
API
===

ViewSet options
---------------

ViewSet options are attributes that can be set on a viewset class. They
are used to configure the viewset. The following options are available:

The most common attributes for the viewset mixins in the provided code are:

- ``model``: The Django model class associated with the viewset.
- ``fields``: A list of fields to be used in the view for display or form input.
- ``layout``: A nested list specifying how the fields should be layed out. See :ref:`Layouts for fields`.
- ``queryset``: The queryset used to fetch the data for the view.
- ``inline_classes``: A list of related inline classes for the view, see the Inlines section below.
- ``form_class``: The form class used for handling form submissions in the view.
- ``link_layout``: A list of facets that will be linked from within the user interface, see :ref:`Links between views`.

.. TODO: This is the same text as Usage/Common viewset options. Should this be
   removed from here?

List view
^^^^^^^^^
The list view shows a paginated, searchable, sortable list of items. It
can be configured using the following viewset attributes:


- ``list_sort_fields``
    Specify which fields are sortable. The ``list_sort_fields_columns`` attribute can be
    used to specify the column name in the database. By default, the
    column name is the same as the field name.
- ``list_search_fields``
    Add a search field to the list view.
    This attribute should be a list of fields that will be searched.
- ``list_item_link_layout``
    Specify which links should be shown
    for each item in the list. See :ref:`Links between views` for more.
- ``list_link_layout``
    Specify which links should be shown at the top of the list.
    See :ref:`Links between views` for more.
- ``list_filterset_fields``
    Specify which fields should be used for filtering using
    `django-filter <https://django-filter.readthedocs.io/en/stable/>`_.
    This attribute should be a list of field names.
    For more control, you can specify a custom ``FilterSet`` using the ``list_filterset_class`` attribute.
- ``list_action_classes``
    Specify actions that can be applied to all selected items in the list.
    See :ref:`Actions` for more.

.. TODO: add API description for other views

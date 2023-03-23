=============
Usage
=============

.. _ViewSets usage:

ViewSets
--------
ViewSets are used to group and configure several views for a single model,
somewhat similar to django-rest-framework. They allow you to define and
manage configuration for different views, such as list, create, update,
and detail views. By specifying attributes on the viewset you can customize
the behaviour of all views.

The viewset figures out which attributes should be passed to which view and also takes into account
the specificity. If you specify both ``fields`` and ``list_fields``, the list view will receive
the latter, while all others will receive the former.

The default ``beam.ViewSet`` class provides a ``create``, ``list``, ``detail``, ``update``, and ``delete`` view.

Here's an example of a ``ViewSet`` for a model called Book where the fields for the list view differ from
those for all other views.

.. code-block:: python

    # books/views.py
    import beam
    from .models import Book

    class BookViewSet(beam.ViewSet):
        model = Book
        fields = ["title", "author", "publication_date", "price"]
        list_fields = ["title", "author"]

    # urls.py
    from books.views import BookViewSet
    urlpatterns = [
        url(r"^books/$", BookViewSet.as_view()),
    ]




Common viewset options
^^^^^^^^^^^^^^^^^^^^^^
The most common attributes for the viewset mixins in the provided code are:

- ``model``: The Django model class associated with the viewset.
- ``fields``: A list of fields to be used in the view for display or form input.
- ``layout``: A nested list specifying how the fields should be layed out. See :ref:`Layouts for fields`.
- ``queryset``: The queryset used to fetch the data for the view.
- ``inline_classes``: A list of related inline classes for the view, see the Inlines section below.
- ``form_class``: The form class used for handling form submissions in the view.
- ``link_layout``: A list of components that will be linked from within the user interface, see :ref:`Links between views`.

For a complete list of attributes, see the documentation for the respective viewset mixins.

.. _Layouts for fields:

Layouts for fields
^^^^^^^^^^^^^^^^^^

Beam layouts are a simple way to give forms and detail views
some structure without the use of custom templates.
By specifying a tripple nested list on the viewset, fields can be grouped into
rows and columns. The default theme supports up to 4 columns per row.

.. code-block:: python

    layout = [
        [ # first row
            ["name", "age",],   # first column
            ["email", "phone"],   # second column
        ]
        [ # second row
            ["a", "b",],   # first column
            ["c", "d",],   # second column
        ]
    ]

The example above would result in the following layout:

.. code-block::

    +-----------------------------------------------+
    |         name                   email          |
    |         age                    phone number   |
    +-----------------------------------------------+
    |          a                       c            |
    |          b                       d            |
    +-----------------------------------------------+

Most of the time the  elements of the nested list will be strings which are mapped to form / model fields.
If you need more controlyou can pass a ``VirtualField`` for a regular field with a label or
you can pass ``HTML`` to render whatever you want.

.. code-block:: python

    from beam.layouts import VirtualField, HTML

    class ExampleViewSet(beam.ViewSet):
        model = Example
        fields = ["name", "phone"]
        layout = [[
            [
            "name",
            VirtualField(
                "phone",
                lambda obj: mark_safe(obj.phone_as_link),
                verbose_name=_("phone"))
            ],
            [
            HTML("<h1>Some HTML</h1>")
            ]
        ]]




.. _Links between views:

Links between views
^^^^^^^^^^^^^^^^^^^^
Beam shows links to other views in the viewset both at the top of all pages
as well as next to items in the list page. Those links are controlled using the ``link_layout`` attribute.

The following things can be specified in the link layout:

- ``"prefix"``: A string means that a link to the view "prefix_view" on the same viewset will be view added.
- ``"!prefix"``: A string prefixed with an exclamation mark means that "prefix_view" will be hidden.
- ``"..."``: All views that are not explicitly specified will be added here.


If you e.g. want the create view to be the only one shown at the top of the list view, set
``list_link_layout = ["create"]``.

For a more complicated example, you could specify the link layout for the detail view as follows:
This would cause create to be hidden, the first link to be to the update view, the last one to
the delete view and all others would show up in between those two.

.. code-block:: python

    class BookViewSet(beam.ViewSet):
        model = Book
        fields = ["title", "author"]
        detail_link_layout = ["update", "...", "delete", "!create"]
        list_link_layout = ["create]


The list view also shows links next to each list item.
To specify the links shown for each list item, set ``list_item_link_layout``.


Inlines
-------
Inlines are a way to display and edit related models within the same form or view of a parent model.

There are two types of inline classes, the regular ``beam.RelatedInline`` and ``beam.TabularInline``.
The regular inline uses multiple rows to display the related model, while the tabular inline uses
a table row for each related instance.

To use inlines, you'll need to create a custom inline class for the related model, typically by subclassing RelatedInline, and add it to the inline_classes attribute of the relevant viewset mixin (e.g., list_inline_classes, create_inline_classes, etc.). This will automatically integrate the inlines into the viewset, making it easier to manage the relationship between the models within the user interface.

In the example below you'll be able to create, edit and view books from the respective author views.

.. code-block:: python

    # books/views.py
    import beam
    from .models import Book, Author

    class BookInline(beam.RelatedInline):
        model = Book
        fk_field = "author"
        fields = ["title"]

    class AuthorViewSet(beam.ViewSet):
        model = Author
        fields = ["name"]
        inline_classes = [BookInline]

    # urls.py
    from books.views import BookViewSet
    urlpatterns = [
        url(r"^books/$", BookViewSet.as_view()),
    ]


If you need to use different inlines for e.g. the detail and the update view, just create two different inline classes and add
pass one of them to the ``detail_inline_classes`` and the other to the ``update_inline_classes`` attribute.


Adding views: Components
------------------------

Components are used to group and pass relevant attributes from the viewset to
the individual views. A view is only passed data that it's component expects in
`__init__`. The component provides methods like ``has_perm`` to check if the user
has the required permissions to access the relevant view or ``reverse`` to link
to the view.

You only need to care about components if you want to extend a viewset with
additional views as in the example below.

.. code-block:: python

    class CustomerCallView(beam.views.ComponentMixin, MyBaseView):
        phone = None
        # your custom view code goes here ...

    class CustomerViewSet(beam.ViewSet):
        model = Customer
        fields = ["first_name", "last_name", "email", "phone"]

        call_component = Component
        call_url = "call/{phone}/"
        call_url_kwargs = {"phone": "phone"}
        call_permission = "customers.view_customer"


Overriding templates
---------------------

Beam uses the class based views from Django's generic views. This means that
when you create a template ``<app_label>/<model_name><template_name_suffix>.html``
it will be used for the respective view. For example, if you have a
model ``customers.Customer`` and create a template ``customers/customer_detail.html``
it will be used for the detail view of the ``CustomerViewSet``.

Beam also provides a default template for each view.

``beam/create.html``, ``beam/update.html``, ``beam/detail.html``, ``beam/delete.html``, ``beam/list.html``

You can override these templates by creating a template with the same name in your app's ``templates`` directory.

They are all based on the same base template ``beam/base.html`` which you can also override.
The base template is also the place where you can add custom CSS and JS.

.. _Actions:

Actions
-------
You can use actions to add custom functionality to list views. Actions are
displayed as a dropdown at the top of the list view. When the user clicks on the apply
button, the action's ``apply`` method is called with the selected
objects as arguments.

Actions can provide a ``form`` attribute which will be used to display a form
when the action is selected. The form can be used to collect additional
options from the user.

An action can be added to the list view by adding it to the ``list_actions`` attribute.

The below example will add a button to the list view which will send an email
with the given subject and message to all selected customers.

.. code-block:: python

    from django.core.mail import send_mail
    import beam
    from beam.actions import Action

    class SendEmailAction(Action):
        label = _("Send email")
        form = SendEmailForm

        def apply(self, request, queryset):
            send_mail(
                self.form.cleaned_data["subject"],
                self.form.cleaned_data["message"],
                "no-reply@example.com",
                queryset.objects.values_list("email", flat=True)
            )

        def get_success_message(self):
            return _("Sent {count} emails").format(
                count=self.count,
            )

    class CustomerViewSet(beam.ViewSet):
        model = Customer
        fields = ["first_name", "last_name", "email", "phone"]
        list_actions = [SendEmailAction]

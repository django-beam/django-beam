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

    # books/models.py
    class Book(models.Model):
        title = models.CharField(max_length=255)
        author = models.ForeignKey("Author", on_delete=models.CASCADE, related_name="books")
        # add these two fields
        publication_date = models.DateField()
        price = models.DecimalField(max_digits=5, decimal_places=2)

    # books/views.py
    import beam
    from .models import Book

    class BookViewSet(beam.ViewSet):
        model = Book
        fields = ["title", "author", "publication_date", "price"]
        list_fields = ["title", "author"]


Common viewset options
^^^^^^^^^^^^^^^^^^^^^^
The most common attributes for the viewset mixins in the provided code are:

- ``model``: The Django model class associated with the viewset.
- ``fields``: A list of fields to be used in the view for display or form input.
- ``layout``: A nested list specifying how the fields should be layed out. See :ref:`Layouts for fields`.
- ``queryset``: The queryset used to fetch the data for the view.
- ``inline_classes``: A list of related inline classes for the view, see the Inlines section below.
- ``form_class``: The form class used for handling form submissions in the view.
- ``link_layout``: A list of facets that will be linked from within the user interface, see :ref:`Links between views`.


.. TODO For a complete list of attributes, see the documentation for the respective viewset mixins.

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
        ],
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

    # books/models.py
    class Book(models.Model):
        title = models.CharField(max_length=255)
        author = models.ForeignKey("Author", on_delete=models.CASCADE, related_name="books")
        publication_date = models.DateField()
        price = models.DecimalField(max_digits=5, decimal_places=2)
        isbn = models.CharField(max_length=255, null=True, blank=True)


    # books/views.py
    from beam.layouts import VirtualField, HTML
    from django.utils.html import escape
    from django.utils.safestring import mark_safe
    from .models import Book

    class BookViewSet(beam.ViewSet):
        model = Book
        fields = ["title", "author", "publication_date", "price"]
        layout = [
            [  # row 1
                ["title", "author"],            # first column
                ["publication_date", "price"],  # second column
            ],
            [  # row 2
                [
                    VirtualField(
                        name="isbn_search",
                        callback=lambda obj: mark_safe(f'<a href="https://www.isbnsearch.org/isbn/{escape(obj.isbn)}">Search ISBN</a>'),
                        verbose_name="ISBN Search"
                    ),
                ],
                [
                    HTML("<h1>Hey! I'm a label for a book!</h1>")
                ],
            ],
        ]
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

    import beam
    from .models import Book

    class BookViewSet(beam.ViewSet):
        model = Book
        fields = ["title", "author"]
        detail_link_layout = ["update", "...", "delete", "!create"]
        list_link_layout = ["create"]
        ...

The list view also shows links next to each list item.
To specify the links shown for each list item, set ``list_item_link_layout``.


Inlines
-------
Inlines are a way to display and edit related models within the same form or view of a parent model.

There are two types of inline classes, the regular ``beam.RelatedInline`` and ``beam.inlines.TabularRelatedInline``.
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
        foreign_key_field = "author"
        fields = ["title"]

    class AuthorViewSet(beam.ViewSet):
        model = Author
        fields = ["name"]
        # add this line
        inline_classes = [BookInline]

If you need to use different inlines for e.g. the detail and the update view, just create two different inline classes and add
pass one of them to the ``detail_inline_classes`` and the other to the ``update_inline_classes`` attribute.


Adding views: Facets
------------------------

Facets are used to group and pass relevant attributes from the viewset to
the individual views. A view is only passed data that it's facet expects in
`__init__`. The facet provides methods like ``has_perm`` to check if the user
has the required permissions to access the relevant view or ``reverse`` to link
to the view.

You only need to care about facets if you want to extend a viewset with
additional views as in the example below.

In the follow up example we introduce a "call" facet to the author view.

.. code-block:: python

    # books/views.py
    import beam
    from django.views.generic import TemplateView
    from beam.views import Facet
    from .models import Author

    class AuthorViewSet(beam.ViewSet):
        model = Author
        fields = ["name"]

        # add these lines
        call_facet = Facet
        call_url = "<str:pk>/call/"
        call_url_kwargs = {"pk": "pk"}
        call_permission = "authors.view_author"
        call_view_class = AuthorCallView
        call_verbose_name = "Call author!"

    class AuthorCallView(beam.views.FacetMixin, TemplateView):
        phone = None
        template_name = "authors/author_call.html"

         # pass author from kwargs to context for template
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            author_pk = self.kwargs.get("pk", None)

            try:
                context["author"] = Author.objects.get(pk=author_pk)
            except Author.DoesNotExist:
                pass

            return context


    # books/templates/authors/author_call.html
    # See next section for overriding templates
    {% extends "beam/detail.html" %}
    {% block details_container %}
        Calling {{ author.title }} ... ring ring!
    {% endblock %}

Overriding templates
---------------------

Beam uses the class based views from Django's generic views. This means that
when you create a template ``<app_label>/<model_name><template_name_suffix>.html``
it will be used for the respective view. For example, if you have a
model ``customers.Customer`` and create a template ``customers/customer_detail.html``
it will be used for the detail view of the ``CustomerViewSet``.

Beam also adds a template name based on the facet name. For example, if you
have a facet ``call_facet`` and create a template ``customers/customer_call.html``
it will be used for the call view.

Beam also provides default templates for all base view.

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

    # books/models.py
    from django.db import models

    class Email(models.Model):
        subject = models.CharField(max_length=255)
        message = models.TextField()
        recipient = models.EmailField()


    # books/forms.py
    from django import forms
    from .models import Email

    class SendEmailForm(forms.ModelForm):
        class Meta:
            model = Email
            fields = ["subject", "message", "recipient"]


    # books/actions.py
    from django.core.mail import send_mail
    import beam
    from beam.actions import Action

    class SendEmailAction(Action):
        label = "Send email"
        form = SendEmailForm

        def apply(self, request, queryset):
            send_mail(
                self.form.cleaned_data["subject"],
                self.form.cleaned_data["message"],
                "no-reply@example.com",
                queryset.objects.values_list("email", flat=True)
            )

        def get_success_message(self):
            return "Sent {count} emails".format(
                count=self.count,
            )


    # books/views.py
    import beam
    from .models import Author
    from .actions import SendEmailAction

    class AuthorViewSet(beam.ViewSet):
        model = Author
        fields = ["name"]

        # add this line
        list_actions = [SendEmailAction]

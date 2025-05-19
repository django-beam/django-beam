==========================
Frequently asked questions
==========================


- How do I add a link to a view that is not part of the viewset?
    You can override the links property of the viewset to add links to other views.
    In the example below we add a "frontend" button that will show up e.g. on the detail page


    .. code-block:: python

        class SomeViewSet(beam.ViewSet)
            # ...
            @property
            def links(self) -> Dict[str, BaseFacet]:
                links = super().links
                links["frontend"] = Link(
                    viewset=self,
                    name="frontend",
                    verbose_name=_("frontend"),
                    url_name="uploads_upload_frontend",
                    url_kwargs={"public_id": "public_id"},
                    permission="uploads.view_frontend",
                )
                return links

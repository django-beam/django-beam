
urlpatterns += [
    path(
        "admin/search_and_replace/",
        SearchAndReplaceView.as_view(
            models_and_fields=[(Cat, ("name", "bio")), (Dog, ("name", "bark"))]
        ),
        name="search-and-replace",
    )
]

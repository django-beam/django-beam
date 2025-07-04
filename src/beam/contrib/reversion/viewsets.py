from contextlib import contextmanager
from typing import Iterable, List

from django.utils.translation import gettext_lazy as _
from reversion import (
    create_revision,
    get_comment,
    is_registered,
    register,
    set_comment,
    set_user,
)

from beam import RelatedInline, ViewSet
from beam.urls import UrlKwargDict
from beam.viewsets import BaseViewSet, DeleteMixin, DetailMixin, Facet, UpdateMixin

from .views import VersionDetailView, VersionListView, VersionRestoreView


class VersionRestoreMixin(BaseViewSet):
    version_restore_view_class = VersionRestoreView
    version_restore_url = "<str:pk>/versions/<str:version_id>/restore/"
    version_restore_url_kwargs: UrlKwargDict = {"pk": "pk"}
    version_restore_verbose_name = None
    version_restore_url_name = None
    version_restore_link_layout: List[str] = []
    version_restore_permission = "{app_label}.change_{model_name}"

    def get_facet_classes(self):
        return super().get_facet_classes() + [("version_restore", Facet)]


class VersionDetailMixin(BaseViewSet):
    version_detail_view_class = VersionDetailView
    version_detail_url = "<str:pk>/versions/<str:version_id>/"
    version_detail_url_kwargs: UrlKwargDict = {"pk": "pk"}
    version_detail_verbose_name = _("show version")
    version_detail_url_name = None
    version_detail_link_layout = ["version_list"]
    version_detail_permission = "{app_label}.view_{model_name}"

    detail_link_layout = DetailMixin.detail_link_layout + ["!version_detail"]

    def get_facet_classes(self):
        return super().get_facet_classes() + [("version_detail", Facet)]

    # mirror the detail fields and layout
    @property
    def version_detail_fields(self):
        return getattr(self, "detail_fields", getattr(self, "fields", []))

    @property
    def version_detail_layout(self):
        return getattr(self, "detail_layout", getattr(self, "layout", []))

    @property
    def version_detail_inline_classes(self):
        return getattr(
            self, "detail_inline_classes", getattr(self, "inline_classes", [])
        )


class VersionListMixin(BaseViewSet):
    version_list_view_class = VersionListView
    version_list_url = "<str:pk>/versions/"
    version_list_url_kwargs: UrlKwargDict = {"pk": "pk"}
    version_list_verbose_name = _("history")
    version_list_url_name = None
    version_list_link_layout = ["detail"]
    version_list_permission = "{app_label}.view_{model_name}"

    def get_facet_classes(self):
        return super().get_facet_classes() + [("version_list", Facet)]


class VersionViewSetMixin(VersionDetailMixin, VersionRestoreMixin, VersionListMixin):
    versioned_facet_names = ["create", "update", "delete"]
    update_link_layout = UpdateMixin.update_link_layout + [
        "!version_restore",
        "!version_detail",
    ]
    delete_link_layout = DeleteMixin.delete_link_layout + [
        "!version_restore",
        "!version_detail",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.register_model_and_inlines_with_reversion(
            self.model, self._get_version_inline_classes()
        )

    def _get_version_inline_classes(self):
        """
        Get all inline classes that are shown in versioned views.
        """
        return {
            inline_class
            for facet in self.facets.values()
            for inline_class in facet.inline_classes
            if facet.name in self.versioned_facet_names
        }

    def _register_model_with_parents(self, model, follow=()):
        """
        Register a model with reversion automatically accounting for multi table inheritance.
        """
        if is_registered(model):
            return

        follow = tuple(follow)

        # recursively register parents to support multi table inheritance as per api docs
        # https://django-reversion.readthedocs.io/en/stable/api.html#registration-api
        for parent_model, field in model._meta.concrete_model._meta.parents.items():
            follow += (field.name,)
            self._register_model_with_parents(parent_model, ())

        register(model, follow=follow)

    def register_model_and_inlines_with_reversion(
        self, model, inline_classes: Iterable[RelatedInline]
    ):
        """
        Register the model and all inline models with reversion
        iff they haven't been registered before.

        If you want full control over which models are versioned together,
        register them with reversion manually.
        """
        if is_registered(model):
            return

        # we collect all inline fields so that reversion knows
        # which inline instances to include in revisions.
        inline_fields = []
        for inline_class in inline_classes:
            inline_model = inline_class.model
            inline_model_opts = inline_class.model._meta

            # do not register inlines that have their own viewset, this yields confusing
            # behaviour as they may not be registered on their own
            if (
                inline_model_opts.app_label in self.registry
                and inline_model_opts.model_name
                in self.registry[inline_model_opts.app_label]
            ):
                continue

            # register the inline model
            self._register_model_with_parents(inline_model)

            # if the remote field has an accessor name that
            # we can follow from our model (not hidden)
            # we want reversion to follow that accessor when
            # creating a revision for our model
            if not inline_model._meta.get_field(
                inline_class.foreign_key_field
            ).remote_field.hidden:
                field = inline_model._meta.get_field(inline_class.foreign_key_field)
                inline_fields.append(field.remote_field.get_accessor_name())

        self._register_model_with_parents(model, inline_fields)

    @contextmanager
    def create_revision(self, request):
        with create_revision():
            if request.user.is_authenticated:
                set_user(request.user)
            yield

    def _set_revision_comment(self, facet, request, *args, **kwargs):
        """
        Sets the revision comment according to facet and parameters.
        """
        if not get_comment():
            comment = facet.verbose_name
            set_comment(comment)

    def _get_view(self, facet):
        """
        Ensure that the views in `self.versioned_facet_names`
        are wrapped with the create_revision context_manager
        """
        view = super()._get_view(facet)
        if facet.name not in self.versioned_facet_names:
            return view

        def wrapped_view(request, *args, **kwargs):
            with self.create_revision(request):
                self._set_revision_comment(facet, request, *args, **kwargs)
                return view(request, *args, **kwargs)

        return wrapped_view


class VersionViewSet(VersionViewSetMixin, ViewSet):
    pass

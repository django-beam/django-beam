from contextlib import contextmanager
from typing import Iterable

from django.utils.translation import ugettext_lazy as _
from reversion import (
    register,
    create_revision,
    set_user,
    is_registered,
    set_comment,
    get_comment,
)

from beam import RelatedInline
from beam import ViewSet
from beam.viewsets import BaseViewSet, Component
from .views import VersionDetailView, VersionListView


class VersionDetailMixin(BaseViewSet):
    version_detail_view_class = VersionDetailView
    version_detail_url = "<str:pk>/versions/<str:version_id>/"
    version_detail_url_kwargs = ["pk"]
    version_detail_verbose_name = _("show version")
    version_detail_url_name = None
    version_detail_link_layout = ["version_list"]

    def get_component_classes(self):
        return super().get_component_classes() + [("version_detail", Component)]


class VersionListMixin(BaseViewSet):
    version_list_view_class = VersionListView
    version_list_url = "<str:pk>/versions/"
    version_list_url_kwargs = ["pk"]
    version_list_verbose_name = _("history")
    version_list_url_name = None
    version_list_link_layout = ["detail"]

    def get_component_classes(self):
        return super().get_component_classes() + [("version_list", Component)]


class VersionViewSetMixin(VersionDetailMixin, VersionListMixin):
    versioned_component_names = ["create", "update"]

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
            for component in self.components.values()
            for inline_class in component.inline_classes
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
        Register the model and all inline models with reversion iff they haven't been registered before.

        If you want full control over which models are versioned together, register them with reversion manually.
        """
        if is_registered(model):
            return

        # we collect all inline fields so that reversion knows which inline instances to include in revisions.
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

            # if the remote field has an accessor name that we can follow from our model (not is_hidden())
            # we want reversion to follow that accessor when creating a revision for our model
            if not inline_model._meta.get_field(
                inline_class.foreign_key_field
            ).remote_field.is_hidden():
                field = inline_model._meta.get_field(inline_class.foreign_key_field)
                inline_fields.append(field.remote_field.get_accessor_name())

        self._register_model_with_parents(model, inline_fields)

    @contextmanager
    def create_revision(self, request):
        with create_revision():
            if request.user.is_authenticated:
                set_user(request.user)
            yield

    def _set_revision_comment(self, component, request, *args, **kwargs):
        """
        Sets the revision comment according to component and parameters.
        """
        if not get_comment():
            comment = component.verbose_name
            set_comment(comment)

    def _get_view(self, component):
        """
        Ensure that the views in `self.versioned_component_names` are wrapped with the create_revision context_manager
        """
        view = super()._get_view(component)
        if component.name not in self.versioned_component_names:
            return view

        def wrapped_view(request, *args, **kwargs):
            with self.create_revision(request):
                self._set_revision_comment(component, request, *args, **kwargs)
                return view(request, *args, **kwargs)

        return wrapped_view


class VersionViewSet(VersionViewSetMixin, ViewSet):
    pass

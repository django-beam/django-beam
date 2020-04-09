from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.views import generic
from reversion import set_comment, RevertError
from reversion.models import Version

from beam.views import ViewSetContextMixin, DetailView


class _RollBackRevisionView(Exception):
    def __init__(self, response) -> None:
        super().__init__()
        self.response = response


class VersionDetailView(DetailView):
    def get_context_data(self, **kwargs):
        kwargs["version"] = self.version
        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        self.version = get_object_or_404(
            Version.objects.get_for_object_reference(self.model, kwargs["pk"]),
            pk=kwargs["version_id"],
        )

        # Check that database transactions are supported.
        if not connection.features.uses_savepoints:
            raise ImproperlyConfigured(
                "Cannot use VersionAdmin with a database that does not support savepoints."
            )

        # Run the view.
        try:
            with transaction.atomic(using=self.version.db):
                self.version.revision.revert(delete=True)
                response = super().get(request, *args, **kwargs)
                if hasattr(response, "render"):
                    response.render()
                raise _RollBackRevisionView(
                    response
                )  # Raise exception to undo the transaction and revision.
        except RevertError as ex:
            messages.error(request, force_text(ex))
            return HttpResponseRedirect(
                self.viewset.links["version_list"].reverse(self.version.object)
            )
        except _RollBackRevisionView as ex:
            return ex.response

    def get_template_names(self):
        return ["beam_reversion/version_detail.html"]


class VersionRestoreView(DetailView):
    def get_context_data(self, **kwargs):
        kwargs["version"] = self.version
        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        self.version = get_object_or_404(
            Version.objects.get_for_object_reference(self.model, kwargs["pk"]),
            pk=kwargs["version_id"],
        )
        return HttpResponseRedirect(
            self.viewset.links["version_detail"].reverse(
                self.version.object, version_id=self.version.pk
            )
        )

    def post(self, request, *args, **kwargs):
        self.version = get_object_or_404(
            Version.objects.get_for_object_reference(self.model, kwargs["pk"]),
            pk=kwargs["version_id"],
        )

        # Check that database transactions are supported.
        if not connection.features.uses_savepoints:
            raise ImproperlyConfigured(
                "Cannot use VersionAdmin with a database that does not support savepoints."
            )

        # Run the view.
        try:
            with transaction.atomic(using=self.version.db):
                # Revert the revision.
                with self.viewset.create_revision(request):
                    set_comment(_("revert to version {}".format(self.version.pk)))
                    self.version.revision.revert(delete=True)
                    messages.success(request, "Reverted")
                    return HttpResponseRedirect(
                        self.viewset.links["detail"].reverse(self.version.object)
                    )
        except RevertError as ex:
            messages.error(request, force_text(ex))
            return HttpResponseRedirect(
                self.viewset.links["detail"].reverse(self.version.object)
            )

    def get_template_names(self):
        return ["beam_reversion/version_detail.html"]


class VersionListView(ViewSetContextMixin, generic.DetailView):
    def get_template_names(self):
        return ["beam_reversion/version_list.html"]

    def get_context_data(self, **kwargs):
        kwargs["versions"] = Version.objects.get_for_object(self.object)
        return super().get_context_data(**kwargs)

from beam.registry import register
from beam.viewsets import default_registry
from django.apps import apps
from django.views import generic
from django.views.generic.base import ContextMixin, TemplateView


class ViewSetContextMixin(ContextMixin):
    viewset_context = None
    links = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "viewset_context" not in context:
            context["viewset_context"] = self.viewset_context
        if "links" not in context:
            context["links"] = self.links
        return context

    @property
    def model(self):
        if self.viewset_context["model"] is not None:
            return self.viewset_context["model"]
        return super().model

    def get_queryset(self):
        if self.viewset_context["queryset"] is not None:
            return self.viewset_context["queryset"]
        return super().get_queryset()

    @property
    def fields(self):
        if self.viewset_context["fields"] is not None:
            return self.viewset_context["fields"]
        return super().fields


class CreateView(ViewSetContextMixin, generic.CreateView):

    def get_template_names(self):
        return super().get_template_names() + ["beam/create.html"]

    def get_success_url(self):
        return self.links["detail"].get_url(obj=self.object)


class UpdateView(ViewSetContextMixin, generic.UpdateView):

    def get_template_names(self):
        return super().get_template_names() + ["beam/update.html"]

    def get_success_url(self):
        return self.links["detail"].get_url(obj=self.object)


class ListView(ViewSetContextMixin, generic.ListView):

    def get_template_names(self):
        return super().get_template_names() + ["beam/list.html"]


class DetailView(ViewSetContextMixin, generic.DetailView):

    def get_template_names(self):
        return super().get_template_names() + ["beam/detail.html"]


class DeleteView(ViewSetContextMixin, generic.DeleteView):

    def get_template_names(self):
        return super().get_template_names() + ["beam/delete.html"]

    def get_success_url(self):
        return self.links["list"].get_url()


class DashboardView(TemplateView):
    template_name = "beam/dashboard.html"

    viewsets = None
    registry = default_registry

    def build_registry(self, viewsets):
        registry = {}
        for viewset in viewsets:
            register(registry, viewset)
        return registry

    def get_registry(self):
        if self.viewsets:
            return self.build_registry(self.viewsets)
        else:
            return self.registry

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        grouped = []
        for app_label, viewsets_dict in self.get_registry().items():
            group = {
                "app_label": app_label,
                "app_config": apps.get_app_config(app_label),
                "viewsets": viewsets_dict.values(),
            }
            grouped.append(group)
        context["grouped_by_app"] = grouped
        return context

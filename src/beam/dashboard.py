from django.template.loader import get_template
from django.views.generic import TemplateView

class DashboardView(TemplateView):
    page_heading = "Dashboard"
    template_name = 'beam/dashboard.html'

    viewsets = []
    title = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = [
            {
                'name': viewset.model._meta.verbose_name_plural,
                'list_url_name': viewset.get_url_name('list'),
                'create_url_name': viewset.get_url_name('create'),
            }
            for viewset in self.viewsets
        ]
        context['page_heading'] = self.page_heading
        return context



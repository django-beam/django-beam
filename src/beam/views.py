from django.views import generic


class CreateView(generic.CreateView):

    def get_template_names(self):
        return super().get_template_names() + ["beam/create.html"]


class UpdateView(generic.UpdateView):

    def get_template_names(self):
        return super().get_template_names() + ["beam/update.html"]


class ListView(generic.ListView):

    def get_template_names(self):
        return super().get_template_names() + ["beam/list.html"]


class DetailView(generic.DetailView):

    def get_template_names(self):
        return super().get_template_names() + ["beam/detail.html"]


class DeleteView(generic.DeleteView):

    def get_template_names(self):
        return super().get_template_names() + ["beam/delete.html"]

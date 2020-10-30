from beam.actions import DeleteAction
from django.test import TestCase
from django_webtest import WebTest
from test_views import user_with_perms
from testapp.models import Dragonfly
from testapp.views import DragonFlyUpdateAction, DragonflyViewSet


class ActionTest(TestCase):
    def test_delete_action(self):
        action = DeleteAction(
            data=None, model=Dragonfly, id="delete-dragonfly", request=None
        )
        Dragonfly.objects.create(name="alpha", age=10)
        Dragonfly.objects.create(name="beta", age=10)
        Dragonfly.objects.create(name="gamma", age=100)
        action.apply(Dragonfly.objects.filter(age__lte=10))
        self.assertEqual(action.get_success_message(), "Deleted 2 dragonflys")
        self.assertEqual(Dragonfly.objects.count(), 1)

    def test_mass_update_action(self):
        Dragonfly.objects.create(name="alpha", age=10)
        Dragonfly.objects.create(name="beta", age=10)
        Dragonfly.objects.create(name="gamma", age=100)

        action = DragonFlyUpdateAction(
            data={"update-age": "100"}, model=Dragonfly, id="update", request=None
        )
        action.apply(Dragonfly.objects.all())

        self.assertEqual(action.get_success_message(), "Updated 2 dragonflys")
        self.assertEqual(Dragonfly.objects.filter(age=100).count(), 3)


class ActionViewTest(WebTest):
    def setUp(self):
        self.alpha = Dragonfly.objects.create(name="alpha", age=12)
        self.omega = Dragonfly.objects.create(name="omega", age=99)

    def test_no_action_selected_does_nothing(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_select[]"] = [self.alpha.pk]
        response = form.submit()
        self.assertContains(response, "alpha")
        self.assertContains(response, "omega")
        self.assertEqual(Dragonfly.objects.count(), 2)

    def test_no_list_items_selected_does_nothing(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"] = "0-delete"
        response = form.submit().follow()
        self.assertContains(response, "alpha")
        self.assertContains(response, "omega")
        self.assertEqual(Dragonfly.objects.count(), 2)

    def test_action_with_selection(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"] = "0-delete"
        form["_action_select[]"] = [self.alpha.pk]
        response = form.submit().follow()

        self.assertNotContains(response, "alpha")
        self.assertContains(response, "omega")

        self.assertEqual(Dragonfly.objects.count(), 1)

    def test_selection_across_page_boundary(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"] = "0-delete"
        form["_action_select_across"] = "all"
        response = form.submit().follow()

        self.assertNotContains(response, "alpha")
        self.assertNotContains(response, "omega")

        self.assertEqual(Dragonfly.objects.count(), 0)

    def test_no_permission_hides_action_from_menu(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.change_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        with self.assertRaises(ValueError):
            form["_action_choice"] = "0-delete"

    def test_no_permission_prevents_action(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.change_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"].force_value("0-delete")
        form["_action_select_across"] = "all"
        response = form.submit()

        self.assertContains(response, "alpha")
        self.assertContains(response, "omega")

        self.assertEqual(Dragonfly.objects.count(), 2)

    def test_invalid_form_shows_error_and_preserves_action_choice(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.change_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"] = "1-update_selected"
        form["_action_select[]"] = [self.alpha.pk]
        form["1-update_selected-age"] = "not_a_number"

        response = form.submit()

        self.assertContains(response, "Enter a whole number")
        self.assertEqual(
            response.forms["list-action-form"]["_action_choice"].value,
            "1-update_selected",
        )

    def test_filter_interaction(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse() + "?filter-name=alpha",
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"] = "0-delete"
        form["_action_select_across"] = "all"
        response = form.submit().follow()

        self.assertContains(response, "Deleted 1 dragonflys")

        self.assertFalse(Dragonfly.objects.filter(name="alpha").exists())
        self.assertTrue(Dragonfly.objects.filter(name="omega").exists())

    def test_search_interaction(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse() + "?q=omega",
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"] = "0-delete"
        form["_action_select_across"] = "all"
        response = form.submit().follow()

        self.assertContains(response, "Deleted 1 dragonflys")

        self.assertTrue(Dragonfly.objects.filter(name="alpha").exists())
        self.assertFalse(Dragonfly.objects.filter(name="omega").exists())

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group, Permission
from django.test.utils import override_settings
from django.urls import include, path, reverse
from django_webtest import WebTest
from test_views import user_with_perms

urlpatterns = [
    path("auth/", include("beam.contrib.auth.urls")),
]


@override_settings(ROOT_URLCONF=__name__)
class UserViewTest(WebTest):
    def test_create_user(self):
        create_page = self.app.get(
            reverse("auth_user_create"),
            user=user_with_perms(["auth.add_user", "auth.view_user"]),
        )
        form = create_page.form
        form["username"] = "a.user"
        form["password1"] = "v3rys3cur3"
        form["password2"] = "v3rys3cur3"

        response = form.submit()

        self.assertContains(response.follow(), "a.user")

        user = get_user_model().objects.get(username="a.user")

        self.assertTrue(check_password("v3rys3cur3", user.password))

    def test_update_user(self):
        user = user_with_perms(["auth.delete_group"], username="other.user")
        one_group = Group.objects.create(name="One group")
        other_group = Group.objects.create(name="Other group")
        user.groups.add(one_group)

        update_page = self.app.get(
            reverse("auth_user_update", kwargs={"pk": user.pk}),
            user=user_with_perms(
                ["auth.add_user", "auth.view_user", "auth.change_user"]
            ),
        )

        form = update_page.form

        form["email"] = "a.user@example.com"
        form["groups"] = [other_group.pk]
        form["user_permissions"] = [
            Permission.objects.get(codename="add_group").pk,
            Permission.objects.get(codename="view_group").pk,
        ]

        response = form.submit()

        self.assertContains(response.follow(), "a.user")

        user.refresh_from_db()

        self.assertEqual(user.email, "a.user@example.com")

        self.assertSequenceEqual(user.groups.all(), [other_group])

        self.assertSetEqual(
            set(user.get_all_permissions()), {"auth.add_group", "auth.view_group"}
        )

    def test_user_detail(self):
        user = user_with_perms(["auth.view_group"], username="other.user")
        one_group = Group.objects.create(name="One group")
        Group.objects.create(name="Other group")
        user.groups.add(one_group)

        detail_page = self.app.get(
            reverse("auth_user_detail", kwargs={"pk": user.pk}),
            user=user_with_perms(
                ["auth.add_user", "auth.view_user", "auth.change_user"]
            ),
        )

        self.assertContains(detail_page, "other.user")
        self.assertContains(detail_page, "One group")
        self.assertNotContains(detail_page, "Other group")
        self.assertContains(detail_page, "view_group")
        self.assertNotContains(detail_page, "change_group")

    def test_user_list(self):
        one_user = user_with_perms([], username="one.user")
        other_user = user_with_perms([], username="other.user")
        list_page = self.app.get(
            reverse("auth_user_list"),
            user=user_with_perms(
                ["auth.add_user", "auth.view_user", "auth.change_user"],
                username="admin.user",
            ),
        )
        self.assertContains(list_page, str(one_user))
        self.assertContains(list_page, str(other_user))

    def test_user_list_search(self):
        user_with_perms([], username="one.user")
        user_with_perms([], username="other.user")

        list_page = self.app.get(
            reverse("auth_user_list"),
            user=user_with_perms(
                ["auth.add_user", "auth.view_user", "auth.change_user"],
                username="admin.user",
            ),
        )

        list_page.forms["search-form"]["q"] = "one.u"
        search_response = list_page.forms["search-form"].submit()

        self.assertContains(search_response, "one.user")
        self.assertNotContains(search_response, "other.user")

    def test_user_list_filter(self):
        one_user = user_with_perms([], username="one.user")
        other_user = user_with_perms([], username="other.user")

        other_user.is_superuser = True
        other_user.save()

        one_group = Group.objects.create(name="One group")
        one_group.user_set.add(one_user)
        other_group = Group.objects.create(name="Other group")
        other_group.user_set.add(other_user)

        list_page = self.app.get(
            reverse("auth_user_list"),
            user=user_with_perms(
                ["auth.add_user", "auth.view_user", "auth.change_user"],
            ),
        )

        filter_form = list_page.forms["filter-form"]
        filter_form["filter-groups"] = [one_group.pk]
        filter_response = filter_form.submit()

        self.assertContains(filter_response, "one.user")
        self.assertNotContains(filter_response, "other.user")

        filter_form = list_page.forms["filter-form"]
        filter_form["filter-groups"] = []
        filter_form["filter-is_superuser"] = "true"
        filter_response = filter_form.submit()

        self.assertContains(filter_response, "other.user")
        self.assertNotContains(filter_response, "one.user")

    def test_user_delete(self):
        one_user = user_with_perms(["auth.view_group"], username="one.user")
        one_group = Group.objects.create(name="One group")
        one_group.user_set.add(one_user)

        delete_page = self.app.get(
            reverse("auth_user_delete", kwargs={"pk": one_user.pk}),
            user=user_with_perms(
                ["auth.delete_user", "auth.view_user"],
            ),
        )

        self.assertContains(delete_page, "user-group relationship")
        self.assertContains(delete_page, "user-permission relationship")

        delete_response = delete_page.form.submit()

        self.assertRedirects(delete_response, reverse("auth_user_list"))

        self.assertFalse(get_user_model().objects.filter(pk=one_user.pk).exists())

    def test_user_create_requires_permission(self):
        self.app.get(
            reverse("auth_user_create"),
            user=user_with_perms([], username="no-perms"),
            status=403,
        )
        self.app.get(
            reverse("auth_user_create"),
            user=user_with_perms(["auth.add_user"], username="perms"),
            status=200,
        )

    def test_user_list_requires_permission(self):
        self.app.get(
            reverse("auth_user_list"),
            user=user_with_perms([], username="no-perms"),
            status=403,
        )
        self.app.get(
            reverse("auth_user_list"),
            user=user_with_perms(["auth.view_user"], username="perms"),
            status=200,
        )

    def test_user_detail_requires_permission(self):
        user = user_with_perms([], username="no-perms")
        self.app.get(
            reverse("auth_user_detail", kwargs={"pk": user.pk}),
            user=user,
            status=403,
        )
        self.app.get(
            reverse("auth_user_detail", kwargs={"pk": user.pk}),
            user=user_with_perms(["auth.view_user"], username="perms"),
            status=200,
        )

    def test_user_update_requires_permission(self):
        user = user_with_perms([], username="no-perms")
        self.app.get(
            reverse("auth_user_update", kwargs={"pk": user.pk}),
            user=user,
            status=403,
        )
        self.app.get(
            reverse("auth_user_update", kwargs={"pk": user.pk}),
            user=user_with_perms(["auth.change_user"], username="perms"),
            status=200,
        )

    def test_user_delete_requires_permission(self):
        user = user_with_perms([], username="no-perms")
        self.app.get(
            reverse("auth_user_delete", kwargs={"pk": user.pk}),
            user=user,
            status=403,
        )
        self.app.get(
            reverse("auth_user_delete", kwargs={"pk": user.pk}),
            user=user_with_perms(["auth.delete_user"], username="perms"),
            status=200,
        )


@override_settings(ROOT_URLCONF=__name__)
class GroupViewTest(WebTest):
    def test_group_create_requires_permission(self):
        self.app.get(
            reverse("auth_group_create"),
            user=user_with_perms([], username="no-perms"),
            status=403,
        )
        self.app.get(
            reverse("auth_group_create"),
            user=user_with_perms(["auth.add_group"], username="perms"),
            status=200,
        )

    def test_group_list_requires_permission(self):
        self.app.get(
            reverse("auth_group_list"),
            user=user_with_perms([], username="no-perms"),
            status=403,
        )
        self.app.get(
            reverse("auth_group_list"),
            user=user_with_perms(["auth.view_group"], username="perms"),
            status=200,
        )

    def test_group_detail_requires_permission(self):
        group = Group.objects.create()
        self.app.get(
            reverse("auth_group_detail", kwargs={"pk": group.pk}),
            user=user_with_perms([], username="no-perms"),
            status=403,
        )
        self.app.get(
            reverse("auth_group_detail", kwargs={"pk": group.pk}),
            user=user_with_perms(["auth.view_group"], username="perms"),
            status=200,
        )

    def test_group_update_requires_permission(self):
        group = Group.objects.create()
        self.app.get(
            reverse("auth_group_update", kwargs={"pk": group.pk}),
            user=user_with_perms([], username="no-perms"),
            status=403,
        )
        self.app.get(
            reverse("auth_group_update", kwargs={"pk": group.pk}),
            user=user_with_perms(["auth.change_group"], username="perms"),
            status=200,
        )

    def test_group_delete_requires_permission(self):
        group = Group.objects.create()
        self.app.get(
            reverse("auth_group_delete", kwargs={"pk": group.pk}),
            user=user_with_perms([], username="no-perms"),
            status=403,
        )
        self.app.get(
            reverse("auth_group_delete", kwargs={"pk": group.pk}),
            user=user_with_perms(["auth.delete_group"], username="perms"),
            status=200,
        )

    def test_create_group(self):
        create_page = self.app.get(
            reverse("auth_group_create"),
            user=user_with_perms(["auth.add_group", "auth.view_group"]),
        )
        form = create_page.form
        form["name"] = "A group"
        form["permissions"] = [Permission.objects.get(codename="view_user").pk]

        response = form.submit()

        self.assertContains(response.follow(), "A group")
        self.assertContains(response.follow(), "view_user")

        group = Group.objects.get(name="A group")

        self.assertTrue(group.permissions.filter(codename="view_user").exists())

    def test_update_group(self):
        group = Group.objects.create(name="One group")
        group.permissions.add(Permission.objects.get(codename="view_user"))

        update_page = self.app.get(
            reverse("auth_group_update", kwargs={"pk": group.pk}),
            user=user_with_perms(["auth.change_group", "auth.view_group"]),
        )

        form = update_page.form

        form["name"] = "1 group"

        form["permissions"] = [
            Permission.objects.get(codename="view_group").pk,
            Permission.objects.get(codename="change_group").pk,
        ]
        response = form.submit()

        self.assertContains(response.follow(), "1 group")

        group.refresh_from_db()

        self.assertEqual(group.name, "1 group")

        self.assertSetEqual(
            set(group.permissions.values_list("codename", flat=True)),
            {"change_group", "view_group"},
        )

    def test_group_detail(self):
        user = user_with_perms(["auth.view_group"], username="a.user")
        group = Group.objects.create(name="One group")
        group.permissions.add(Permission.objects.get(codename="view_user"))
        group.user_set.add(user)

        detail_page = self.app.get(
            reverse("auth_group_detail", kwargs={"pk": group.pk}),
            user=user,
        )

        self.assertContains(detail_page, "One group")
        self.assertContains(detail_page, "view_user")
        self.assertContains(detail_page, "a.user")

    def test_group_delete(self):
        user = user_with_perms(
            ["auth.view_group", "auth.delete_group"], username="a.user"
        )
        group = Group.objects.create(name="One group")
        group.permissions.add(Permission.objects.get(codename="view_user"))
        group.user_set.add(user)

        delete_page = self.app.get(
            reverse("auth_group_delete", kwargs={"pk": group.pk}),
            user=user,
        )

        self.assertContains(delete_page, "user-group relationship")
        self.assertContains(delete_page, "group-permission relationship")

        delete_response = delete_page.form.submit()

        self.assertRedirects(delete_response, reverse("auth_group_list"))

        self.assertFalse(Group.objects.filter(pk=group.pk).exists())

    def test_group_list(self):
        Group.objects.create(name="One group")
        Group.objects.create(name="Other group")
        list_page = self.app.get(
            reverse("auth_group_list"),
            user=(user_with_perms(["auth.view_group"], username="a.user")),
        )
        self.assertContains(list_page, "One group")
        self.assertContains(list_page, "Other group")

    def test_group_list_search(self):
        Group.objects.create(name="One group")
        Group.objects.create(name="Other group")

        list_page = self.app.get(
            reverse("auth_group_list"),
            user=(user_with_perms(["auth.view_group"], username="a.user")),
        )

        search_from = list_page.forms["search-form"]
        search_from["q"] = "Other"
        search_results = search_from.submit()

        self.assertNotContains(search_results, "One group")
        self.assertContains(search_results, "Other group")

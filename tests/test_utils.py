from beam.utils import check_permission, navigation_component_entry
from django.test import TestCase
from test_views import user_with_perms
from testapp.views import DragonflyViewSet, SightingViewSet


class CheckPermissionsTest(TestCase):
    def test_check_no_permission_implies_true(self):
        self.assertTrue(check_permission(None, user=user_with_perms([]), obj=None))

    def test_check_string_permission(self):
        user = user_with_perms(["testapp.change_dragonfly"])

        self.assertTrue(
            check_permission("testapp.change_dragonfly", user=user, obj=user)
        )
        self.assertFalse(
            check_permission("testapp.view_dragonfly", user=user, obj=user)
        )

    def test_check_callable_permission(self):
        user = user_with_perms([])

        def check(user, obj=None):
            return user == obj

        self.assertTrue(check_permission(check, user=user, obj=user))
        self.assertFalse(check_permission(check, user=user, obj=None))

    def test_check_any_permission_with_no_user_implies_false(self):
        self.assertFalse(check_permission(lambda *args: True, user=None, obj=None))

    def test_navigation_entry_handles_empty(self):
        self.assertEqual(navigation_component_entry(None), None)

    def test_navigation_entry_uses_model_name_as_list_label(self):
        user = user_with_perms(["testapp.view_dragonfly"])
        self.assertEqual(
            navigation_component_entry(DragonflyViewSet().links["list"], user=user),
            ("dragonflys", "/dragonfly/"),
        )

    def test_navigation_entry_handles_other_components(self):
        user = user_with_perms(["testapp.view_sighting"])
        self.assertEqual(
            navigation_component_entry(
                SightingViewSet().links["other_list"], user=user
            ),
            ("Another list is possible", "/sighting/other/"),
        )

    def test_navigation_entry_respects_permissions(self):
        user = user_with_perms(["testapp.view_dragonfly"])
        self.assertEqual(
            navigation_component_entry(DragonflyViewSet().links["list"], user=user),
            ("dragonflys", "/dragonfly/"),
        )
        self.assertEqual(
            navigation_component_entry(SightingViewSet().links["list"], user=user), None
        )

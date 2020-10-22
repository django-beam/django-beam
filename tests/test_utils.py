from beam.utils import check_permission
from django.test import TestCase
from test_views import user_with_perms


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

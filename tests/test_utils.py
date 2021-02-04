from unittest import mock

from django.test import TestCase
from django.urls import NoReverseMatch
from test_views import user_with_perms
from testapp.views import DragonflyViewSet, SightingViewSet

from beam.utils import check_permission, navigation_component_entry, reverse_component


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

    def test_reverse_component_returns_url(self):
        url = reverse_component(
            component=DragonflyViewSet().links["list"],
            request=None,
            obj=None,
            override_kwargs=None,
        )
        self.assertEqual(url, "/dragonfly/")

    def test_reverse_component_raises_no_reverse_match_if_no_reverse_match(self):
        with self.assertRaises(NoReverseMatch) as e:
            reverse_component(
                component=DragonflyViewSet().links["detail"],
                request=None,
                obj=None,
                override_kwargs=None,
            )
        self.assertIsInstance(e.exception, NoReverseMatch)
        self.assertTrue(
            str(e.exception).startswith(
                "Unable to reverse url to "
                "<Component testapp.views.DragonflyViewSet 'detail'>: "
                "Reverse"
            )
        )

    def test_reverse_component_raises_on_all_exceptions(self):
        component = DragonflyViewSet().links["detail"]
        with mock.patch.object(
            component, "resolve_url", side_effect=ValueError("FAIL")
        ):
            with self.assertRaises(Exception) as e:
                reverse_component(
                    component=component, request=None, obj=None, override_kwargs=None
                )
        self.assertNotIsInstance(e.exception, NoReverseMatch)
        self.assertEqual(
            str(e.exception),
            "Unable to reverse url to <Component testapp.views.DragonflyViewSet 'detail'>: FAIL",
        )

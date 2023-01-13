from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, Permission
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

import beam.inlines
from beam import ViewSet
from beam.contrib.auth.forms import GroupForm, UserUpdateForm
from beam.layouts import VirtualField


class GroupInline(beam.inlines.RelatedInline):
    model = Group
    foreign_key_field = "nope"
    layout = [
        [
            [
                VirtualField(
                    "group",
                    callback=lambda obj: obj,
                    verbose_name=Group._meta.get_field("name").verbose_name,
                )
            ]
        ]
    ]

    def get_prefix(self):
        return "groups"

    def get_queryset(self):
        return Group.objects.filter(user=self.parent_instance)


class UserPermissionInline(beam.inlines.TabularRelatedInline):
    model = Permission
    foreign_key_field = "nope"
    fields = ["name", "content_type", "codename"]

    def get_prefix(self):
        return "permissions"

    def get_queryset(self):
        return Permission.objects.filter(user=self.parent_instance).select_related(
            "content_type"
        )


class UserViewSet(ViewSet):
    model = get_user_model()

    detail_inline_classes = [UserPermissionInline, GroupInline]

    detail_layout = [
        [
            [
                "username",
                "first_name",
                "last_name",
                "email",
                "is_active",
                "is_staff",
                "is_superuser",
                VirtualField(
                    "dates_header",
                    lambda obj: "",
                    verbose_name=mark_safe(
                        "<h4 class='mt-2'>{}</h4>".format(_("Important dates"))
                    ),
                ),
                "last_login",
                "date_joined",
            ]
        ]
    ]
    update_layout = [
        [["username", "email"]],
        [["first_name", "last_name"]],
        [["is_active", "is_staff", "is_superuser"]],
        [["groups"]],
        [["user_permissions"]],
        [["last_login", "date_joined"]],
    ]
    list_fields = [
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
    ]
    list_sort_fields = list_fields
    list_search_fields = ["username", "email", "first_name", "last_name"]
    list_filterset_fields = ["is_active", "is_staff", "is_superuser", "groups"]

    create_form_class = UserCreationForm
    update_form_class = UserUpdateForm


class UserInline(beam.inlines.RelatedInline):
    model = get_user_model()
    foreign_key_field = "nope"
    layout = [
        [
            [
                VirtualField(
                    "user",
                    callback=lambda obj: obj,
                    verbose_name=get_user_model()._meta.verbose_name,
                )
            ]
        ]
    ]

    def get_prefix(self):
        return "users"

    def get_queryset(self):
        return get_user_model().objects.filter(groups=self.parent_instance)


class GroupPermissionInline(beam.inlines.TabularRelatedInline):
    model = Permission
    foreign_key_field = "nope"
    fields = ["name", "content_type", "codename"]

    def get_prefix(self):
        return "permissions"

    def get_queryset(self):
        return Permission.objects.filter(group=self.parent_instance).select_related(
            "content_type"
        )


class GroupViewSet(ViewSet):
    model = Group
    list_fields = ["name"]
    fields = ["name", "permissions"]
    list_search_fields = ["name"]
    list_sort_fields = ["name"]
    detail_inline_classes = [GroupPermissionInline, UserInline]
    detail_fields = [
        "name",
    ]
    form_class = GroupForm

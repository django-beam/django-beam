from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .widgets import BootstrapSelectMultiple


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        ]
        widgets = {
            "groups": BootstrapSelectMultiple(),
            "user_permissions": BootstrapSelectMultiple(),
        }


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = [
            "name",
            "permissions",
        ]
        widgets = {
            "permissions": BootstrapSelectMultiple(),
        }

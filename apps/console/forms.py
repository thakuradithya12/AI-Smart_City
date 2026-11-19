from django import forms

from apps.accounts.models import User
from apps.geography.models import Department


class RouteComplaintForm(forms.Form):
    department = forms.ModelChoiceField(queryset=Department.objects.order_by("name"), required=False)
    reason = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))


class RejectComplaintForm(forms.Form):
    reason = forms.CharField(min_length=3, widget=forms.Textarea(attrs={"rows": 2}))


class TransferComplaintForm(forms.Form):
    reason = forms.CharField(min_length=3, widget=forms.Textarea(attrs={"rows": 2}))


class AssignComplaintForm(forms.Form):
    assignee = forms.ModelChoiceField(queryset=User.objects.none())

    def __init__(self, *args, department, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignee"].queryset = User.objects.filter(
            role=User.Role.FIELD_WORKER,
            department=department,
            is_active=True,
        ).order_by("name")

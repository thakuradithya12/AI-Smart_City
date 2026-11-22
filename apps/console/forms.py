from django import forms

from apps.accounts.models import User
from apps.geography.models import Department


class RouteComplaintForm(forms.Form):
    department = forms.ModelChoiceField(queryset=Department.objects.order_by("name"), required=False)
    reason = forms.CharField(required=False, min_length=5, max_length=500, widget=forms.Textarea(attrs={"rows": 2, "minlength": 5, "maxlength": 500}))


class DuplicateLinkForm(forms.Form):
    duplicate_of = forms.IntegerField(min_value=1)


class RejectComplaintForm(forms.Form):
    reason = forms.CharField(min_length=5, max_length=500, widget=forms.Textarea(attrs={"rows": 2, "minlength": 5, "maxlength": 500}))


class TransferComplaintForm(forms.Form):
    reason = forms.CharField(min_length=5, max_length=500, widget=forms.Textarea(attrs={"rows": 2, "minlength": 5, "maxlength": 500}))


class MessageForm(forms.Form):
    message = forms.CharField(min_length=5, max_length=2000, widget=forms.Textarea(attrs={"rows": 3}))


class ReasonForm(forms.Form):
    reason = forms.CharField(min_length=5, max_length=500, widget=forms.Textarea(attrs={"rows": 3, "minlength": 5, "maxlength": 500}))


class FieldEvidenceForm(forms.Form):
    kind = forms.ChoiceField(choices=(("field_before", "Before work"), ("field_after", "After work")))
    photo = forms.ImageField()


class WorkDoneForm(forms.Form):
    note = forms.CharField(min_length=5, max_length=2000, widget=forms.Textarea(attrs={"rows": 3}))


class VerifyForm(forms.Form):
    method = forms.ChoiceField(choices=(("site_review", "Site review"), ("citizen_confirmation", "Citizen confirmation")))


class AssignComplaintForm(forms.Form):
    assignee = forms.ModelChoiceField(queryset=User.objects.none())

    def __init__(self, *args, department, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignee"].queryset = User.objects.filter(
            role=User.Role.FIELD_WORKER,
            department=department,
            is_active=True,
        ).order_by("name")

from django import forms
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import User
from apps.geography.models import Category


class CitizenRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "name")

    def clean_password1(self):
        password = self.cleaned_data["password1"]
        validate_password(password, self.instance)
        return password

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.role = User.Role.CITIZEN
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ReportForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))
    photo = forms.ImageField()
    latitude = forms.DecimalField(min_value=-90, max_value=90, max_digits=10, decimal_places=7)
    longitude = forms.DecimalField(min_value=-180, max_value=180, max_digits=10, decimal_places=7)
    gps_accuracy_m = forms.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2)
    consent = forms.BooleanField(label="I agree to the privacy notice.")
    pin_confirmed = forms.BooleanField(label="I confirm this pin marks the problem location.")


class ComplaintQueryForm(forms.Form):
    pass

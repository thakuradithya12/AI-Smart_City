import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import User
from apps.accounts.phone_numbers import normalize_phone_number
from apps.geography.models import Category


class CitizenRegistrationForm(forms.ModelForm):
    phone_number = forms.CharField(
        label="Phone number",
        max_length=24,
        help_text="Indian mobile number, for example 9876543210 or +91 98765 43210.",
        widget=forms.TelInput(attrs={"autocomplete": "tel", "inputmode": "tel", "placeholder": "+91 98765 43210"}),
    )
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("phone_number", "name")

    def clean_phone_number(self):
        try:
            phone_number = normalize_phone_number(self.cleaned_data["phone_number"])
        except ValidationError as exc:
            raise ValidationError("Enter a valid Indian mobile number.") from exc
        if User.objects.filter(phone_number=phone_number).exists():
            raise ValidationError("An account already uses this phone number. Sign in or use another number.")
        return phone_number

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
        user.phone_number = self.cleaned_data["phone_number"]
        user.email = None
        user.username = user.phone_number
        user.role = User.Role.CITIZEN
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class PhoneAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Phone number",
        max_length=254,
        widget=forms.TextInput(attrs={
            "type": "tel",
            "autofocus": True,
            "autocomplete": "tel",
            "inputmode": "tel",
            "placeholder": "+91 98765 43210",
        }),
    )

    def clean_username(self):
        identifier = self.cleaned_data["username"].strip()
        try:
            return normalize_phone_number(identifier)
        except ValidationError:
            # Normalize old staff email identifiers so formatting cannot bypass lockout keys.
            return re.sub(r"\s+", "", identifier).casefold()


class ReportForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))
    photo = forms.ImageField(
        widget=forms.ClearableFileInput(
            attrs={"accept": "image/jpeg,image/png,image/webp", "capture": "environment"}
        )
    )
    latitude = forms.DecimalField(min_value=-90, max_value=90, max_digits=10, decimal_places=7)
    longitude = forms.DecimalField(min_value=-180, max_value=180, max_digits=10, decimal_places=7)
    gps_accuracy_m = forms.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2)
    consent = forms.BooleanField(label="I agree to the privacy notice.")
    pin_confirmed = forms.BooleanField(label="I confirm this pin marks the problem location.")


class ComplaintQueryForm(forms.Form):
    pass

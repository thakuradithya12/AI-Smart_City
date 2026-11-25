from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError

from apps.accounts.phone_numbers import normalize_phone_number


class PhoneOrLegacyEmailBackend(ModelBackend):
    """Authenticate new accounts by phone; retain email login only for unmigrated staff."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get("phone_number")
        if not identifier or password is None:
            return None

        User = get_user_model()
        try:
            phone_number = normalize_phone_number(identifier)
        except ValidationError:
            # Existing provisioned accounts keep access until an admin assigns their phone.
            email = str(identifier).strip()
            user = User.objects.filter(phone_number__isnull=True, email__iexact=email).first() if "@" in email else None
        else:
            user = User.objects.filter(phone_number=phone_number).first()

        if user is None:
            # Keep the password-hash work similar for unknown identifiers and known users.
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


def axes_username(request, credentials):
    """Use the same canonical identifier for Axes lockout keys as login lookup."""
    identifier = credentials.get("username") or credentials.get("phone_number") or ""
    try:
        return normalize_phone_number(identifier)
    except ValidationError:
        # Legacy staff emails are case-insensitive; normalize other invalid input too.
        return str(identifier).strip().casefold()

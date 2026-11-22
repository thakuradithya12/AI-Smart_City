import re

from django.core.exceptions import ValidationError


_MOBILE_INDIAN = re.compile(r"[6-9][0-9]{9}\Z")
_E164_INDIAN = re.compile(r"\+91[6-9][0-9]{9}\Z")


def normalize_phone_number(value):
    """Normalize the supported Indian mobile formats to +91XXXXXXXXXX."""
    value = re.sub(r"[\s().-]", "", str(value or ""))
    if value.startswith("0091"):
        value = "+91" + value[4:]
    elif value.startswith("91") and len(value) == 12:
        value = "+" + value
    elif value.startswith("0") and len(value) == 11:
        value = value[1:]

    if _MOBILE_INDIAN.fullmatch(value):
        return "+91" + value
    if _E164_INDIAN.fullmatch(value):
        return value
    raise ValidationError("Enter a valid Indian mobile number, such as 9876543210 or +91 98765 43210.")

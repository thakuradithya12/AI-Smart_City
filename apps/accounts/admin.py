from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib import admin
from apps.accounts.phone_numbers import normalize_phone_number
from .models import User

class AdminUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "phone_number", "email", "name", "role", "department")

    def clean_phone_number(self):
        value = self.cleaned_data.get("phone_number")
        if not value:
            return None
        return normalize_phone_number(value)

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = AdminUserCreationForm
    list_display = ("phone_number", "email", "name", "role", "department", "is_active", "is_staff")
    list_filter = ("role", "department", "is_active", "is_staff")
    ordering = ("phone_number", "email")
    fieldsets = (
        (None, {"fields": ("phone_number", "email", "password")} ),
        ("Profile", {"fields": ("name", "role", "department")} ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")} ),
        ("Important dates", {"fields": ("last_login", "date_joined")} ),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("username", "phone_number", "email", "name", "role", "department", "password1", "password2")} ),)
    search_fields = ("phone_number", "email", "name")

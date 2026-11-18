from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib import admin

from .models import User

class AdminUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "name", "role", "department")

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = AdminUserCreationForm
    list_display = ("email", "name", "role", "department", "is_active", "is_staff")
    list_filter = ("role", "department", "is_active", "is_staff")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")} ),
        ("Profile", {"fields": ("name", "role", "department")} ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")} ),
        ("Important dates", {"fields": ("last_login", "date_joined")} ),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("username", "email", "name", "role", "department", "password1", "password2")} ),)
    search_fields = ("email", "name")

from django.contrib.auth.views import LoginView

from apps.complaints.forms import PhoneAuthenticationForm


class WorkspaceLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = PhoneAuthenticationForm
    redirect_authenticated_user = True

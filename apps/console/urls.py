from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import path
from apps.complaints.views import complaint_detail, evidence_file, my_complaints, register, report

@login_required
def home(request):
    return render(request, "home.html")

urlpatterns = [
    path("", home, name="home"),
    path("register/", register, name="register"),
    path("complaints/new/", report, name="report"),
    path("complaints/", my_complaints, name="my_complaints"),
    path("complaints/<int:pk>/", complaint_detail, name="complaint_detail"),
    path("evidence/<int:pk>/", evidence_file, name="evidence_file"),
]

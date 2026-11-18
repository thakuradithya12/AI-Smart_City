from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import path

@login_required
def home(request):
    return render(request, "home.html")

urlpatterns = [path("", home, name="home")]

from django.contrib import admin

from .models import Category, Department, RoutingRule, Ward

admin.site.register((Category, Department, RoutingRule, Ward))

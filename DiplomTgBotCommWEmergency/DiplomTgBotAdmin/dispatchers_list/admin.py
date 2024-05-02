from django.contrib import admin
from .models import DispatcherItem


@admin.register(DispatcherItem)
class DispatcherItem(admin.ModelAdmin):
    list_display = "id", "user_id", "username"
    list_display_links = "id", "user_id", "username"
    ordering = "id",

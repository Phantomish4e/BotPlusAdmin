from django.contrib import admin
from .models import UserItem


@admin.register(UserItem)
class UserItem(admin.ModelAdmin):
    list_display = "id", "user_id", "username"
    list_display_links = "id", "user_id", "username"
    ordering = "id",

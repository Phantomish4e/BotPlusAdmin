from django.contrib import admin
from django.db import models
from .models import IncidentItem


@admin.register(IncidentItem)
class IncindentItem(admin.ModelAdmin):
    list_display = "id", "type", "sender_id", "sender_name", "description", "sender_location", "place", "date"
    ordering = "id",

    def CountTypeIncident(self, request, queryset):
        duplicates = IncidentItem.objects.values('type').annotate(count=models.Count('type')).filter(count__gt=1)
        return duplicates

    def duplicates_count(self, obj):
        return obj['count']

    CountTypeIncident.short_description = 'Count Type Incidents'
    actions = ['CountTypeIncident']


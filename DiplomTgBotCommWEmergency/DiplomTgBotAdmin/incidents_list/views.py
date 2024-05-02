from django.shortcuts import render
from .models import IncidentItem
from django.core import serializers
from django.http import JsonResponse


def dashboard_incident_list(request):
    return render(request, 'dashboard_incident_list.html', {})


def pivot_data(request):
    dataset = IncidentItem.objects.all()
    data = serializers.serialize('json', dataset)
    return JsonResponse(data, safe=False)

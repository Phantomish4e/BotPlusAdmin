from django.db import models


class IncidentItem(models.Model):
    class Meta:
        db_table = 'Incidents'
        verbose_name = 'incident'

    type = models.CharField(max_length=45)
    sender_id = models.IntegerField()
    sender_name = models.CharField(max_length=45)
    description = models.CharField(max_length=45)
    sender_location = models.CharField(max_length=45)
    place = models.CharField(max_length=45)
    date = models.DateField()

    def __str__(self):
        return self.type


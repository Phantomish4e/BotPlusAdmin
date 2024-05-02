from django.db import models


class DispatcherItem(models.Model):
    class Meta:
        db_table = 'Dispatchers'
        verbose_name = 'dispatcher'

    user_id = models.IntegerField()
    username = models.CharField(max_length=45)

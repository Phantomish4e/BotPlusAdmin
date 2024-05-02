from django.db import models


class UserItem(models.Model):
    class Meta:
        db_table = 'Users'
        verbose_name = 'telegram user'

    user_id = models.IntegerField()
    username = models.CharField(max_length=45)

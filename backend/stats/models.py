from django.db import models


class Mission(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.TextField()
    description = models.TextField(default='', null=True)
    xp_reward = models.IntegerField(default=50, null=True)
    course_id = models.TextField(null=True)
    sort_order = models.IntegerField(default=0, null=True)
    is_active = models.BooleanField(default=True, null=True)
    correct_condition = models.TextField(default='', null=True)
    correct_action = models.TextField(default='', null=True)

    class Meta:
        db_table = 'missions'
        managed = False


class UserDailyXpLog(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(null=True)
    log_date = models.DateField()
    xp_earned = models.IntegerField(default=0, null=True)

    class Meta:
        db_table = 'user_daily_xp_logs'
        managed = False
        unique_together = (('user_id', 'log_date'),)

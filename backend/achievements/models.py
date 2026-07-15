from django.db import models


class Achievement(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.TextField(unique=True)
    name = models.TextField()
    description = models.TextField(null=True)
    icon = models.TextField(null=True)
    condition_type = models.TextField()   # lesson_count | streak_days | xp_total | course_complete
    condition_value = models.IntegerField()

    class Meta:
        db_table = 'achievements'
        managed = False


class UserAchievement(models.Model):
    pk = models.CompositePrimaryKey('user_id', 'achievement_id')
    user_id = models.IntegerField()
    achievement_id = models.IntegerField()
    awarded_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'user_achievements'
        managed = False

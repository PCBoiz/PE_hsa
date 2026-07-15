from django.db import models


class Lesson(models.Model):
    id = models.AutoField(primary_key=True)
    course_id = models.TextField(null=True)
    module = models.TextField(default='', null=True)
    title = models.TextField()
    content = models.TextField(default='', null=True)
    sort_order = models.IntegerField(default=0, null=True)
    created_at = models.DateTimeField(null=True)
    lesson_type = models.TextField(default='reading', null=True)
    xp_reward = models.IntegerField(default=0, null=True)
    is_free_preview = models.BooleanField(default=False, null=True)
    lesson_code = models.TextField(null=True)
    content_json = models.JSONField(null=True)
    subtitle = models.TextField(null=True)
    estimated_minutes = models.IntegerField(null=True)
    updated_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'lessons'
        managed = False


class LessonProgress(models.Model):
    pk = models.CompositePrimaryKey('user_id', 'lesson_id')
    user_id = models.IntegerField()
    lesson_id = models.IntegerField()
    course_id = models.TextField(null=True)
    status = models.TextField(default='in_progress', null=True)  # in_progress | completed
    quiz_score = models.IntegerField(null=True)
    xp_earned = models.IntegerField(default=0, null=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'lesson_progress'
        managed = False

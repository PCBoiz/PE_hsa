from django.db import models


class Course(models.Model):
    id = models.TextField(primary_key=True)
    title = models.TextField(null=True)
    subtitle = models.TextField(null=True)
    description = models.TextField(null=True)
    image = models.TextField(null=True)
    level = models.TextField(null=True)
    duration = models.TextField(null=True)
    students = models.TextField(null=True)
    rating = models.FloatField(null=True)
    lessons = models.IntegerField(null=True)
    color = models.TextField(null=True)
    accent_color = models.TextField(null=True)
    tag = models.TextField(null=True)
    instructor_id = models.IntegerField(null=True)
    xp_reward = models.IntegerField(default=0, null=True)
    is_published = models.BooleanField(default=True, null=True)
    created_at = models.DateTimeField(null=True)
    content_meta = models.JSONField(null=True)

    class Meta:
        db_table = 'courses'
        managed = False


class Enrollment(models.Model):
    pk = models.CompositePrimaryKey('user_id', 'course_id')
    user_id = models.IntegerField()
    course_id = models.TextField()
    progress = models.IntegerField(default=0, null=True)
    completed_lessons = models.IntegerField(default=0, null=True)
    time_spent = models.TextField(default='0h', null=True)
    last_lesson = models.TextField(default='', null=True)
    next_lesson = models.TextField(default='', null=True)
    status = models.TextField(default='active', null=True)
    enrolled_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'enrollments'
        managed = False


class CourseRating(models.Model):
    pk = models.CompositePrimaryKey('user_id', 'course_id')
    user_id = models.IntegerField()
    course_id = models.TextField()
    rating = models.IntegerField()
    created_at = models.TextField(null=True)  # TEXT trong schema gốc

    class Meta:
        db_table = 'course_ratings'
        managed = False

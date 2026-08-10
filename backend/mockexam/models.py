"""Model map 1:1 với bảng mock_exams / mock_attempts (sql/mockexam_schema.sql).
managed=False — DDL do bootstrap_schema tạo; views dùng raw SQL (common/db)."""
from django.db import models


class MockExam(models.Model):
    title = models.TextField()
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.IntegerField(blank=True, null=True)
    total_questions = models.IntegerField(blank=True, null=True)
    questions_json = models.JSONField()
    is_published = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mock_exams'


class MockAttempt(models.Model):
    user_id = models.IntegerField(blank=True, null=True)
    exam_id = models.IntegerField(blank=True, null=True)
    score = models.IntegerField(blank=True, null=True)
    total = models.IntegerField(blank=True, null=True)
    section_scores_json = models.JSONField(blank=True, null=True)
    answers_json = models.JSONField(blank=True, null=True)
    duration_seconds = models.IntegerField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mock_attempts'

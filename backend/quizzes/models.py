from django.db import models


class Quiz(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    course_id = models.TextField()
    status = models.TextField(default='generated', null=True)
    # SNAPSHOT câu hỏi tại thời điểm sinh, KÈM đáp án đúng — chỉ backend đọc
    questions_json = models.JSONField()
    created_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'quizzes'
        managed = False


class ReviewQuizResult(models.Model):
    id = models.AutoField(primary_key=True)
    quiz_id = models.IntegerField()
    user_id = models.IntegerField()
    score = models.IntegerField()
    total = models.IntegerField()
    answers_json = models.JSONField()
    submitted_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'review_quiz_results'
        managed = False

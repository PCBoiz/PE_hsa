# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Achievements(models.Model):
    code = models.TextField(unique=True)
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    icon = models.TextField(blank=True, null=True)
    condition_type = models.TextField()
    condition_value = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'achievements'


class CommentLikes(models.Model):
    pk = models.CompositePrimaryKey('comment_id', 'user_id')
    comment = models.ForeignKey('Comments', models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    reaction_type = models.TextField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'comment_likes'


class Comments(models.Model):
    post = models.ForeignKey('Posts', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    parent_comment = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'comments'


class CourseRatings(models.Model):
    pk = models.CompositePrimaryKey('user_id', 'course_id')
    user = models.ForeignKey('Users', models.DO_NOTHING)
    course = models.ForeignKey('Courses', models.DO_NOTHING)
    rating = models.IntegerField()
    created_at = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'course_ratings'


class Courses(models.Model):
    id = models.TextField(primary_key=True)
    title = models.TextField(blank=True, null=True)
    subtitle = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.TextField(blank=True, null=True)
    level = models.TextField(blank=True, null=True)
    duration = models.TextField(blank=True, null=True)
    students = models.TextField(blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)
    lessons = models.IntegerField(blank=True, null=True)
    color = models.TextField(blank=True, null=True)
    accent_color = models.TextField(blank=True, null=True)
    tag = models.TextField(blank=True, null=True)
    instructor = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    xp_reward = models.IntegerField(blank=True, null=True)
    is_published = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    content_meta = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'courses'


class Enrollments(models.Model):
    pk = models.CompositePrimaryKey('user_id', 'course_id')
    user = models.ForeignKey('Users', models.DO_NOTHING)
    course = models.ForeignKey(Courses, models.DO_NOTHING)
    progress = models.IntegerField(blank=True, null=True)
    completed_lessons = models.IntegerField(blank=True, null=True)
    time_spent = models.TextField(blank=True, null=True)
    last_lesson = models.TextField(blank=True, null=True)
    next_lesson = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    enrolled_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'enrollments'


class LessonProgress(models.Model):
    pk = models.CompositePrimaryKey('user_id', 'lesson_id')
    user = models.ForeignKey('Users', models.DO_NOTHING)
    lesson = models.ForeignKey('Lessons', models.DO_NOTHING)
    course = models.ForeignKey(Courses, models.DO_NOTHING, blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    quiz_score = models.IntegerField(blank=True, null=True)
    xp_earned = models.IntegerField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lesson_progress'


class Lessons(models.Model):
    course = models.ForeignKey(Courses, models.DO_NOTHING, blank=True, null=True)
    module = models.TextField(blank=True, null=True)
    title = models.TextField()
    content = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    lesson_type = models.TextField(blank=True, null=True)
    xp_reward = models.IntegerField(blank=True, null=True)
    is_free_preview = models.BooleanField(blank=True, null=True)
    lesson_code = models.TextField(blank=True, null=True)
    content_json = models.JSONField(blank=True, null=True)
    subtitle = models.TextField(blank=True, null=True)
    estimated_minutes = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lessons'
        unique_together = (('course', 'lesson_code'),)


class Missions(models.Model):
    title = models.TextField()
    description = models.TextField(blank=True, null=True)
    xp_reward = models.IntegerField(blank=True, null=True)
    course = models.ForeignKey(Courses, models.DO_NOTHING, blank=True, null=True)
    sort_order = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    correct_condition = models.TextField(blank=True, null=True)
    correct_action = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'missions'


class NotificationSettings(models.Model):
    user_id = models.IntegerField(primary_key=True)
    email_notif = models.IntegerField(blank=True, null=True)
    push_notif = models.IntegerField(blank=True, null=True)
    study_remind = models.IntegerField(blank=True, null=True)
    content_update = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notification_settings'


class Notifications(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    ref_type = models.TextField(blank=True, null=True)
    ref_id = models.IntegerField(blank=True, null=True)
    is_read = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notifications'


class PlayingWithNeon(models.Model):
    name = models.TextField()
    value = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'playing_with_neon'


class PostLikes(models.Model):
    pk = models.CompositePrimaryKey('post_id', 'user_id')
    post = models.ForeignKey('Posts', models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    reaction_type = models.TextField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'post_likes'


class Posts(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    category = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    content = models.TextField()
    like_count = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'posts'


class Quizzes(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING)
    course = models.ForeignKey(Courses, models.DO_NOTHING)
    status = models.TextField(blank=True, null=True)
    questions_json = models.JSONField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'quizzes'


class ReviewQuizResults(models.Model):
    quiz = models.ForeignKey(Quizzes, models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    score = models.IntegerField()
    total = models.IntegerField()
    answers_json = models.JSONField()
    submitted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'review_quiz_results'


class RoadmapProgress(models.Model):
    pk = models.CompositePrimaryKey('user_id', 'roadmap_id', 'item_id')
    user = models.ForeignKey('Users', models.DO_NOTHING)
    roadmap = models.ForeignKey('Roadmaps', models.DO_NOTHING)
    item_id = models.TextField()
    done = models.BooleanField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roadmap_progress'


class Roadmaps(models.Model):
    id = models.TextField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    source = models.TextField(blank=True, null=True)
    generated_from_survey = models.ForeignKey('Surveys', models.DO_NOTHING, blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    icon = models.TextField(blank=True, null=True)
    color = models.TextField(blank=True, null=True)
    nodes_json = models.JSONField(blank=True, null=True)
    edges_json = models.JSONField(blank=True, null=True)
    mermaid_def = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roadmaps'


class Surveys(models.Model):
    user_id = models.IntegerField(blank=True, null=True)
    data_json = models.JSONField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'surveys'


class UserAchievements(models.Model):
    pk = models.CompositePrimaryKey('user_id', 'achievement_id')
    user = models.ForeignKey('Users', models.DO_NOTHING)
    achievement = models.ForeignKey(Achievements, models.DO_NOTHING)
    awarded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_achievements'


class UserDailyXpLogs(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    log_date = models.DateField()
    xp_earned = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_daily_xp_logs'
        unique_together = (('user', 'log_date'),)


class UserFollows(models.Model):
    pk = models.CompositePrimaryKey('follower_id', 'followee_id')
    follower = models.ForeignKey('Users', models.DO_NOTHING)
    followee = models.ForeignKey('Users', models.DO_NOTHING, related_name='userfollows_followee_set')
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_follows'


class Users(models.Model):
    name = models.TextField(blank=True, null=True)
    email = models.TextField(unique=True, blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    birthday = models.TextField(blank=True, null=True)
    role = models.TextField(blank=True, null=True)
    password = models.CharField(max_length=512, blank=True, null=True)
    streak = models.IntegerField(blank=True, null=True)
    certificates = models.IntegerField(blank=True, null=True)
    gems = models.IntegerField(blank=True, null=True)
    xp = models.IntegerField(blank=True, null=True)
    questionnaire_completed = models.IntegerField(blank=True, null=True)
    last_study_date = models.DateField(blank=True, null=True)
    oauth_provider = models.TextField(blank=True, null=True)
    oauth_provider_id = models.TextField(blank=True, null=True)
    avatar = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
        unique_together = (('oauth_provider', 'oauth_provider_id'),)

from django.db import models


class NotificationSetting(models.Model):
    """Bảng notification_settings — CÀI ĐẶT thông báo (bảng 'notifications' cũ đã rename)."""
    user_id = models.IntegerField(primary_key=True)
    email_notif = models.IntegerField(default=1, null=True)
    push_notif = models.IntegerField(default=0, null=True)
    study_remind = models.IntegerField(default=1, null=True)
    content_update = models.IntegerField(default=0, null=True)

    class Meta:
        db_table = 'notification_settings'
        managed = False


class Notification(models.Model):
    """Bảng notifications — FEED thông báo (chuông)."""
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(null=True)
    type = models.TextField(null=True)      # mention | comment_reply | system ...
    title = models.TextField(null=True)
    body = models.TextField(null=True)
    ref_type = models.TextField(null=True)  # post | comment ...
    ref_id = models.IntegerField(null=True)
    is_read = models.BooleanField(default=False, null=True)
    created_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'notifications'
        managed = False

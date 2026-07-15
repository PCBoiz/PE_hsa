from django.db import models

REACTION_TYPES = ('like', 'love', 'haha', 'wow', 'sad', 'angry')


class Post(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(null=True)
    category = models.TextField(default='discuss', null=True)
    title = models.TextField(default='', null=True)
    content = models.TextField()
    # TỔNG mọi loại reaction — luôn recompute bằng COUNT(*) như bản Flask
    like_count = models.IntegerField(default=0, null=True)
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'posts'
        managed = False


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    post_id = models.IntegerField(null=True)
    user_id = models.IntegerField(null=True)
    content = models.TextField()
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)
    parent_comment_id = models.IntegerField(null=True)  # reply lồng 1 cấp

    class Meta:
        db_table = 'comments'
        managed = False


class PostReaction(models.Model):
    pk = models.CompositePrimaryKey('post_id', 'user_id')
    post_id = models.IntegerField()
    user_id = models.IntegerField()
    reaction_type = models.TextField(default='like')
    created_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'post_likes'
        managed = False


class CommentReaction(models.Model):
    pk = models.CompositePrimaryKey('comment_id', 'user_id')
    comment_id = models.IntegerField()
    user_id = models.IntegerField()
    reaction_type = models.TextField(default='like')
    created_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'comment_likes'
        managed = False

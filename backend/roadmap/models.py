from django.db import models


class Roadmap(models.Model):
    id = models.TextField(primary_key=True)
    user_id = models.IntegerField(null=True)   # NULL = template hệ thống
    source = models.TextField(default='template', null=True)
    generated_from_survey_id = models.IntegerField(null=True)
    title = models.TextField(null=True)
    icon = models.TextField(null=True)
    color = models.TextField(null=True)
    nodes_json = models.JSONField(default=list, null=True)
    edges_json = models.JSONField(default=list, null=True)
    mermaid_def = models.TextField(null=True)
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'roadmaps'
        managed = False


class RoadmapProgress(models.Model):
    pk = models.CompositePrimaryKey('user_id', 'roadmap_id', 'item_id')
    user_id = models.IntegerField()
    roadmap_id = models.TextField()
    item_id = models.TextField()
    done = models.BooleanField(default=False, null=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'roadmap_progress'
        managed = False

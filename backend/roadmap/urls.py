from django.urls import path

from roadmap import views

urlpatterns = [
    path('api/roadmaps', views.RoadmapsView.as_view()),
    path('api/roadmap', views.RoadmapProgressView.as_view()),
    path('api/me/roadmap', views.MyRoadmapView.as_view()),
    path('api/me/roadmap/ai', views.AiRoadmapView.as_view()),
    path('api/roadmap/<str:item_id>', views.UpdateRoadmapItemView.as_view()),
]

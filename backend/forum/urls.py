from django.urls import path

from forum import views

urlpatterns = [
    path('api/posts', views.PostsView.as_view()),
    path('api/posts/<int:post_id>', views.PostDetailView.as_view()),
    path('api/posts/<int:post_id>/react', views.ReactPostView.as_view()),
    path('api/posts/<int:post_id>/comments', views.CommentsView.as_view()),
    path('api/comments/<int:comment_id>/react', views.ReactCommentView.as_view()),
    path('api/comments/<int:comment_id>', views.CommentDetailView.as_view()),
]

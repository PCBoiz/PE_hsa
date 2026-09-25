from django.urls import path

from courseadmin import syllabus, views

urlpatterns = [
    path('api/admin/courses', views.AdminCoursesView.as_view()),
    path('api/admin/courses/<str:course_id>', views.AdminCourseDetailView.as_view()),
    path('api/admin/courses/<str:course_id>/lessons', views.AdminCourseLessonsView.as_view()),
    path('api/admin/lessons', views.AdminLessonsView.as_view()),
    path('api/admin/lessons/<int:lesson_id>', views.AdminLessonDetailView.as_view()),
    # Soạn nội dung 5 bước + nhập cả khoá từ JSON (nhận giáo trình đối tác).
    path('api/admin/lessons/<int:lesson_id>/content', views.AdminLessonContentView.as_view()),
    path('api/admin/courses/<str:course_id>/import', views.AdminCourseImportView.as_view()),

    # ── Khung chương trình theo buổi (E1, §64, 25/09/2026) ──
    path('api/admin/courses/<str:course_id>/syllabus', syllabus.SyllabusVersionsView.as_view()),
    path('api/admin/syllabus/<int:version_id>', syllabus.SyllabusVersionDetailView.as_view()),
    path('api/admin/syllabus/<int:version_id>/sessions', syllabus.SyllabusSessionsView.as_view()),
    path('api/admin/syllabus-sessions/<int:session_id>', syllabus.SyllabusSessionDetailView.as_view()),
    path('api/admin/syllabus-sessions/<int:session_id>/items', syllabus.SyllabusItemsView.as_view()),
    path('api/admin/syllabus-items/<int:item_id>', syllabus.SyllabusItemDetailView.as_view()),
    path('api/admin/syllabus-sessions/<int:session_id>/materials',
         syllabus.SyllabusMaterialsView.as_view()),
    path('api/admin/syllabus-materials/<int:material_id>',
         syllabus.SyllabusMaterialDetailView.as_view()),
    path('api/admin/classes/<int:class_id>/chuong-trinh', syllabus.ClassSyllabusView.as_view()),
]

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard_view'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('logout/', views.logout_view, name='logout_view'),
    path('exam/<int:exam_id>/', views.take_exam_view, name='take_exam'),
    path('courses/add/', views.CourseCreateView.as_view(), name='course_add'),
    path('exams/add/', views.ExamCreateView.as_view(), name='exam_add'),
    path('courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('exam/<int:exam_id>/questions/add/', views.add_question, name='add_question'),
    path('exam/<int:exam_id>/detail/', views.exam_detail, name='exam_detail'),
    path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),

    path('courses/', views.courses_view, name='courses'),
    path('exams/', views.exams_view, name='exams'),
    path('results/', views.results_view, name='results'),
    path('students/', views.students_view, name='students'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('reports/', views.reports_view, name='reports'),
    path('settings/', views.settings_view, name='settings'),

    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
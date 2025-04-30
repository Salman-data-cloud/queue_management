from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('feedback/', views.give_feedback, name='feedback'),
    path('doctor_dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('prioritize/<int:appointment_id>/', views.prioritize_patient, name='prioritize_patient'),
    path('mark_visited/<int:appointment_id>/', views.mark_visited, name='mark_visited'),
    path('skip/<int:appointment_id>/', views.skip_patient, name='skip_patient'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
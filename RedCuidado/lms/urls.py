from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('actividad/', views.activity_board_view, name='activity_board'),
    path('actividad/borrar/<int:entry_id>/', views.delete_bitacora_entry, name='delete_entry'),
    path('rutas/', views.learning_paths_view, name='learning_paths'),
    path('profile/', views.profile_view, name='profile'),
    path('certificate/<int:enrollment_id>/', views.certificate_view, name='certificate'),
    path('course/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('reports/', views.reports_view, name='reports'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('groups/', views.groups_view, name='groups'),
    path('collaborator/create/', views.collaborator_create_view, name='collaborator_create'),
    
    # Management
    path('course/create/', views.course_create_view, name='course_create'),
    path('course/<int:course_id>/edit/', views.course_edit_view, name='course_edit'),
    path('course/<int:course_id>/delete/', views.course_delete_view, name='course_delete'),
    path('course/<int:course_id>/manage/', views.course_manage_view, name='course_manage'),
    path('course/<int:course_id>/test/builder/', views.test_builder_view, name='test_builder'),
    path('course/<int:course_id>/module/add/', views.module_create_view, name='module_add'),
    path('module/<int:module_id>/edit/', views.module_edit_view, name='module_edit'),
    path('module/<int:module_id>/delete/', views.module_delete_view, name='module_delete'),
    path('module/<int:module_id>/content/add/', views.content_create_view, name='content_add'),
    path('content/<int:content_id>/edit/', views.content_edit_view, name='content_edit'),
    path('content/<int:content_id>/delete/', views.content_delete_view, name='content_delete'),
    path('course/<int:course_id>/reorder-modules/', views.reorder_modules, name='reorder_modules'),
    path('module/<int:module_id>/reorder-contents/', views.reorder_contents, name='reorder_contents'),
    
    # Learning / Player
    path('course/<int:course_id>/learn/', views.learning_view, name='course_learn_start'),
    path('course/<int:course_id>/learn/<int:content_id>/', views.learning_view, name='course_learn'),
    path('course/<int:course_id>/take-test/', views.take_test_view, name='take_test'),
    path('course/<int:course_id>/test-result/', views.test_result_view, name='test_result'),
    path('course/<int:course_id>/toggle-pin/', views.toggle_pin_view, name='toggle_pin'),
]

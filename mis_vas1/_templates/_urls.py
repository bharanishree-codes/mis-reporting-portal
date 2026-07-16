from django.urls import path
from mis_vas1.books import *
from mis_vas1.Career_counseeling import *
from mis_vas1.collaborative_students import *
from mis_vas1.competitve_examination import *
from mis_vas1.Courses_project import *
from mis_vas1.Extentions import *
from mis_vas1.Faculty_exchange import *
from mis_vas1.government import *
from mis_vas1.Faculty import *
from mis_vas1.program_offered import *
from mis_vas1.workshop import *
from mis_vas1.Research import *

urlpatterns = [
    path('books/', book_list, name="book_list"),
    path('books/create/', Create, name="Create"),
    path('books/delete/<int:psk_id>/', delete, name='delete'),
    path('books/child/<int:id>/update/', book_update, name='book_update'),

    path('career_counseeling/', career_counseeling_list, name='career_counseeling_list'),
    path('career_counseeling/create/', career_counseeling_create, name='career_counseeling_create'),
    path('career_counseeling/<int:id>/', career_counseeling_view, name='career_counseeling_view'),
    path('career_counseeling/<int:id>/edit/', career_counseeling_update, name='career_counseeling_update'),
    path('career_counseeling/<int:id>/delete/', career_counseeling_delete, name='career_counseeling_delete'),

    path('collaborative_students/', collaborative_students_list, name='collaborative_students_list'),
    path('collaborative_students/create/', collaborative_students_create, name='collaborative_students_create'),
    path('collaborative_students/<int:id>/', collaborative_students_view, name='collaborative_students_view'),
    path('collaborative_students/<int:id>/edit/', collaborative_students_update, name='collaborative_students_update'),
    path('collaborative_students/<int:id>/delete/', collaborative_students_delete,
         name='collaborative_students_delete'),

    path('competitve_examination/', competitve_examination_list, name='competitve_examination_list'),
    path('competitve_examination/create/', competitve_examination_create, name='competitve_examination_create'),
    path('competitve_examination/<int:id>/', competitve_examination_view, name='competitve_examination_view'),
    path('competitve_examination/<int:id>/edit/', competitve_examination_update, name='competitve_examination_update'),
    path('competitve_examination/<int:id>/delete/', competitve_examination_delete,
         name='competitve_examination_delete'),

    path('projects/', project_list, name='project_list'),
    path('projects/create/', project_create, name='project_create'),
    path('projects/<int:id>/', project_view, name='project_view'),
    path('projects/<int:id>/edit/', project_update, name='project_update'),
    path('projects/<int:id>/delete/', project_delete, name='project_delete'),
    path('projects/children/create/<int:id>/<str:val>/', project_child_create, name='project_child_create'),
    path('projects/<int:course_id>/child/<int:child_id>/update/<str:val>/', project_child_update, name='project_child_update'),
    path('projects/<int:course_id>/children/<int:child_id>/delete/', project_child_delete, name='project_child_delete'),

    path('Extension/', extension_list, name='extension_list'),
    path('Extension/create/', extension_create, name='extension_create'),
    path('Extension/<int:id>/', extension_view, name='extension_view'),
    path('Extension/<int:id>/edit/', extension_update, name='extension_update'),
    path('Extension/<int:id>/delete/', extension_delete, name='extension_delete'),

    path('faculty_exchange/', faculty_exchange_list, name='faculty_exchange_list'),
    path('faculty_exchange/create/', faculty_exchange_create, name='faculty_exchange_create'),
    path('faculty_exchange/<int:id>/', faculty_exchange_view, name='faculty_exchange_view'),
    path('faculty_exchange/<int:id>/edit/', faculty_exchange_update, name='faculty_exchange_update'),
    path('faculty_exchange/<int:id>/delete/', faculty_exchange_delete, name='faculty_exchange_delete'),

    path('government_grants/', government_grants_list, name='government_grants_list'),
    path('government_grants/create/', government_grants_create, name='government_grants_create'),
    path('government_grants/<int:id>/', government_grants_view, name='government_grant_view'),
    path('government_grants/<int:id>/edit/', government_grants_update, name='government_grants_update'),
    path('government_grants/<int:id>/delete/', government_grants_delete, name='government_grants_delete'),

    path('participations/', list_participations, name='list_participations'),
    path('participations/create/', create_participation, name='create_participation'),
    path('participations/<int:id>/', detail_view, name='detail_view'),
    path('participations/<int:id>/edit/', update_participation, name='update_participation'),
    path('participations/<int:id>/delete/', delete_participation, name='delete_participation'),
    path('participations/children/', list_all_participation_children,  name='list_participation_children'),
#     path('participations/<int:participation_id>/children/', list_participation_children,  name='list_participation_children'),
    path('participations/children/create/<int:participation_id>/<str:val>/', create_participation_child, name='create_participation_child'),
    path('participations/<int:participation_id>/children/<int:child_id>/update/<str:val>/', update_participation_child,   name='update_participation_child'),
    path('participations/<int:participation_id>/children/<int:child_id>/delete/', delete_participation_child,name='delete_participation_child'),

    path('program/', program_list, name='program_list'),
    path('program/create/', program_create, name='program_create'),
    path('program/<int:id>/', program_view, name='program_view'),
    path('program/<int:id>/edit/', program_update, name='program_update'),
    path('program/<int:id>/delete/', program_delete, name='program_delete'),

    path('workshops/', seminar_list, name='seminar_list'),
    path('workshops/create/', seminar_create, name='seminar_create'),
    path('workshops/<int:id>/', seminar_view, name='seminar_view'),
    path('workshops/<int:id>/edit/', seminar_update, name='seminar_update'),
    path('workshops/<int:id>/delete/', seminar_delete, name='seminar_delete'),

    path('', user_menu, name='user_menu'),
    path('research/', research_list, name='research_list'),
    path('research/create/', research_create, name='research_create'),
    path('research/<int:id>/', research_view, name='research_view'),
    path('research/<int:id>/edit/', research_update, name='research_update'),
    path('research/<int:id>/delete/', research_delete, name='research_delete'),
    path('dashboard/', dashboard, name='dashboard'), 
    # path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('department_dashboard/', department_dashboard, name='department_dashboard'),
    path('admin_dash/', admin_dash, name='admin_dash'),
    path('admin_hod_dash/', admin_hod_dash, name='admin_hod_dash'),
    path('data_fetch/', data_fetch, name='data_fetch'),
    path('pykit_staff_list/', pykit_staff_list, name='pykit_staff_list'),
    path('staff-mails/', mail_validation_filter, name='pykit_staff_list'),
    path('hcas_user/', hcas_user, name='hcas_user'),
]




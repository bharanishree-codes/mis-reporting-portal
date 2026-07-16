from django.urls import path
from .views import *
from .usermaster import *
from .rolesmaster import *
from .userprivilege import *
from .menuelements import *
from .menuprivilege import *
from .settings_views import *
from .user_drf import *

urlpatterns = [

    # DRF

    path('pykit_user/', pykit_user, name='pykit_user'),
    path('pykit_user_id_base/<str:username>/', pykit_user_id_base, name='pykit_user_id_base'),

    path('', user_login, name='user_login'),
    path('home_page/', home_page, name='home_page'),
    # path('home_page/<path:home_page_url>/', home_page, name='home_page'),
    path('get_home_page_url/', get_home_page_url, name='get_home_page_url'),
    path('dropdown_urls_get/', dropdown_urls_get, name='dropdown_urls_get'),
    # path('get_userdetails_ajax/', get_userdetails_ajax, name='get_userdetails_ajax'),
    path('user_profile/', user_profile, name='user_profile'),
    path('list_menus/<int:user_id>/', list_menus, name='list_menus'),
    path('user_menus/<int:user_id>/', user_menus, name='user_menus'),
    path('profile_form_update/<int:user_id>/', profile_form_update, name='profile_form_update'),
    path('reset_password/<int:user_id>/', reset_password, name='reset_password'),
    path('profile_pic_update/<int:user_id>/<int:psk_id>/', profile_pic_update, name='profile_pic_update'),

    path('user_master/<int:user_id>/', user_master_screen, name='user_master_screen'),
    path('create_user_master/<int:user_id>/', create_user_master, name='create_user_master'),
    path('update_user_master/<int:user_id>/<int:psk_id>/', update_user_master, name='update_user_master'),
    path('delete_user_master/<int:user_id>/<str:psk_id>/', delete_user_master, name='delete_user_master'),

    path('role_master/<int:user_id>/', role_master_screen, name='role_master_screen'),
    path('create_role_master/<int:user_id>/', create_role_master, name='create_role_master'),
    path('update_role_master/<int:user_id>/<int:psk_id>/', update_role_master, name='update_role_master'),
    path('delete_role_master/<int:user_id>/<int:psk_id>/', delete_role_master, name='delete_role_master'),

    path('user_privilege_screen/<int:user_id>/', user_privilege_screen, name='user_privilege_screen'),
    path('create_user_privilege/<int:user_id>/', create_user_privilege, name='create_user_privilege'),
    path('update_user_privilege/<int:user_id>/<int:psk_id>/', update_user_privilege, name='update_user_privilege'),
    path('delete_user_privilege/<int:user_id>/<int:psk_id>/', delete_user_privilege, name='delete_user_privilege'),

    path('menu_elements_screen/<int:user_id>/', menu_elements_screen, name='menu_elements_screen'),
    path('create_menu_element/<int:user_id>/', create_menu_element, name='create_menu_element'),
    path('update_menu_element/<int:user_id>/<int:psk_id>/', update_menu_element,
         name='update_menu_element'),
    path('delete_menu_element/<int:user_id>/<int:psk_id>/', delete_menu_element,
         name='delete_menu_element'),

    path('menus_get_insert/', menus_get_insert, name="menus_get_insert"),

    path('menu_privilege_screen/<int:user_id>/', menu_privilege_screen, name='menu_privilege_screen'),
    path('create_menu_privilege/<int:user_id>/', create_menu_privilege, name='create_menu_privilege'),
    path('update_menu_privilege/<int:user_id>/<int:psk_id>/', update_menu_privilege,
         name='update_menu_privilege'),
    path('delete_menu_privilege/<int:user_id>/<int:psk_id>/', delete_menu_privilege,
         name='delete_menu_privilege'),

    path('settings_screen/<int:user_id>', settings_screen, name='settings_screen'),
    path('settings_form/<int:psk_id>/', settings_form, name='settings_form'),

    path('user_master_details/<int:user_id>/', user_master_details, name='user_master_details'),
    path('um_details_form/<int:user_id>/', um_details_form, name='um_details_form'),
    path('edit_um_details_form/<int:user_id>/<int:id>/', edit_um_details_form, name='edit_um_details_form'),

    path('roles_master_details/<int:user_id>/', roles_master_details, name='roles_master_details'),
    path('roles_details_form/<int:user_id>/', roles_details_form, name='roles_details_form'),
    path('edit_roles_details_form/<int:user_id>/<int:id>/', edit_roles_details_form,
         name='edit_roles_details_form'),

    path('user_privi_details/<int:user_id>/', user_privi_details, name='user_privi_details'),
    path('user_privi_form/<int:user_id>/', user_privi_form, name='user_privi_form'),
    path('edit_user_privi_form/<int:user_id>/<int:id>/', edit_user_privi_form,
         name='edit_user_privi_form'),

    path('menu_element_details/<int:user_id>/', menu_element_details, name='menu_element_details'),
    path('menu_element_detail_form/<int:user_id>/', menu_element_detail_form, name='menu_element_detail_form'),
    path('edit_menu_element_detail_form/<int:user_id>/<int:id>/', edit_menu_element_detail_form,
         name='edit_menu_element_detail_form'),

    path('menu_privilege_details/<int:user_id>/', menu_privilege_details, name='menu_privilege_details'),
    path('menu_privilege_detail_form/<int:user_id>/', menu_privilege_detail_form, name='menu_privilege_detail_form'),
    path('edit_menu_privilege_detail_form/<int:user_id>/<int:id>/', edit_menu_privilege_detail_form,
         name='edit_menu_privilege_detail_form'),

    path('get_settings_ajax/', get_settings_ajax, name="get_settings_ajax"),
    path('forgot_password/', reset_password_view, name='reset_password_view'),
    path('confirm_password/<str:encoded_jwt>/<int:psk_id>/', confirm_password_view, name='confirm_password'),

    path('menu_iframe/<int:psk_id>/', menu_iframe_view, name="menu_iframe"),

    path('sneat/', sneat, name="sneat"),
]

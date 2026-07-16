import hashlib
import ast
import datetime
import hashlib
import os
import random
import secrets
import string
import time
import uuid
from datetime import datetime, timedelta

import jwt
import requests as rq
from captcha.image import ImageCaptcha
from django.contrib import auth
from django.contrib.auth.decorators import login_required

from Starter import settings
# ----------------------------------------------------------
from .forms import *
from .menuelements import *
from .models import *
from .settings_views import settings_data, get_settings

import configparser
import os

config = configparser.ConfigParser()
config.read(os.path.join(os.getcwd(), 'config.ini'))

CREATE_USER = config['DEFAULT']['CREATE_USER']

API_STUDIO_URL = user_bundle_settings()

PYKIT_URL = "https://pykit.apistudio.app"


def generate_captcha_text(length=6):
    return ''.join(random.choices(string.ascii_uppercase, k=5))  # Generate 5 random uppercase letters


# Create CAPTCHA image and save it in the static directory
# def create_captcha_image(text, file_name):
#     static_dir = os.path.join(settings.BASE_DIR, "static", "captcha_images")
#     os.makedirs(static_dir, exist_ok=True)  # Ensure the directory exists
#     file_path = os.path.join(static_dir, file_name)
#     image = ImageCaptcha(width=280, height=90)
#     captcha_image = image.generate_image(text)
#     captcha_image.save(file_path)
#     return f"captcha_images/{file_name}"  #


import os
from django.conf import settings
from captcha.image import ImageCaptcha  # Make sure this import is correct


def create_captcha_image(text, file_name):
    media_dir = os.path.join(settings.MEDIA_ROOT, "captcha_images")
    os.makedirs(media_dir, exist_ok=True)  # Ensure the directory exists

    file_path = os.path.join(media_dir, file_name)
    image = ImageCaptcha(width=280, height=90)
    captcha_image = image.generate_image(text)
    captcha_image.save(file_path)

    # Return relative media path
    return f"captcha_images/{file_name}"


@login_required
def get_menu_elements_tbl(request, menus_ids):
    # print("get_menu_elements_tbl")
    menu_uid_list = []

    for menu_id in menus_ids:
        UP_url = f"{API_STUDIO_URL}getapi/asa0502_01_01/{menu_id}"

        payload = {}
        headers = {}

        response = rq.request("GET", UP_url, headers=headers, data=payload)
        # print(response.text)
        user_res_json = response.json()

        if 'psk_id' in user_res_json:
            menu_uid_list.append(user_res_json['psk_id'])
        else:
            print(f"Menu ID {menu_id} not found or invalid response: {user_res_json}")
    # print(menu_uid_list)

    return menu_uid_list


# @login_required
# def get_user_role_value(request, psk_id):
#     # print("get_user_role_value 2")
#     user_data_url = f"{API_STUDIO_URL}getapi/asa0504_01_01/{psk_id}"

#     payload = {}
#     headers = {}

#     response = rq.request("GET", user_data_url, headers=headers, data=payload)
#     # print(response.text)

#     user_res_json = response.json()
#     # print(user_res_json)

#     string_value = user_res_json['user_roles']
#     user_roles = string_value.replace("{", "").replace("}", "")
#     user_roles_value_list = list(map(int, user_roles.split(',')))
#     # print(user_roles)
#     # print(user_roles_value_list)
#     return user_roles_value_list

@login_required
def get_user_role_value(request, psk_id):
    user_data_url = f"{API_STUDIO_URL}getapi/asa0504_01_01/{psk_id}"

    response = rq.request("GET", user_data_url)

    print("RAW RESPONSE:", response.text)

    try:
        user_res_json = response.json()
    except Exception as e:
        print("JSON parse error:", e)
        messages.error(request, "Invalid server response.")
        return None

    print("PARSED JSON:", user_res_json)

    string_value = user_res_json.get('user_roles')

    if not string_value:
        print("user_roles missing or API failed")

        messages.error(request, "User role not found. Please contact admin.")
        return None

    user_roles = string_value.replace("{", "").replace("}", "")
    return user_roles

@login_required
def get_roles_master_tbl(request, psk_id):
    # print("3 . get_roles_master_tbl")
    # print(psk_id)
    psk_id_list = psk_id

    _id_list = []

    for _id in psk_id_list:
        RM_url = f"{API_STUDIO_URL}getapi/asa0501_01_01/{_id}"

        payload = {}
        headers = {}

        response = rq.request("GET", RM_url, headers=headers, data=payload)
        # print(response.text)

        user_res_json = response.json()
        string_value = user_res_json['user_role_privilege']
        # print(string_value)
        _id_list.append(string_value)
    split_values = [int(item) for sublist in _id_list for item in sublist.split(',')]

    # Remove duplicates by converting to a set, then back to a list
    unique_values = list(set(split_values))
    # print(unique_values)
    return unique_values


@login_required
def get_menu_privilege(request):
    # print("4. get_menu_privilege")
    menu_res = rq.get(f"{API_STUDIO_URL}getapi/asa0503_01_01/all")
    menu_privilege = []
    if menu_res.status_code == 200:
        menu_privilege = menu_res.json()
    else:
        messages.error(request, "Unable to connect to API")
    # print(menu_privilege)
    return menu_privilege


@login_required
def get_user_privilege_tbl(request, user_role_privilege_id):
    # print("5. get_user_privilege_tbl")
    UP_url = f"{API_STUDIO_URL}getapi/asa0505_01_01/all"

    payload = {}
    headers = {}

    response = rq.request("GET", UP_url, headers=headers, data=payload)
    # print(response.text)
    user_res_json = response.json()

    get_menu_privilege_tbl = get_menu_privilege(request)
    # print(get_menu_privilege_tbl)

    current_year = datetime.now().year

    output_menus = []

    for date_check in get_menu_privilege_tbl:
        for _id in user_role_privilege_id:
            if date_check['psk_id'] == _id:
                # start_date = datetime.strptime(date_check['menu_privilege_start_date'], "%Y-%m-%d")
                # end_date = date_check['menu_privilege_end_date']
                #
                # current_date = date.today()
                # # print("current_date", current_date)
                # # print("end_date", end_date)
                # # if start_date.year == current_year and current_date != end_date:
                # if start_date.year == current_year and date_check['active'] == "Active":
                #     if end_date is None or current_date <= datetime.strptime(end_date, "%Y-%m-%d").date():
                #         # print(f"Start date is within the current year: {start_date}")
                output_menus.append(_id)

    menus_id = []
    for item in user_res_json:
        for _id in output_menus:
            if int(item['menu_privilege']) == _id:
                menus_id.append(item['menu_items'])

    split_values = [int(item) for sublist in menus_id for item in sublist.split(',')]

    # Remove duplicates by converting to a set, then back to a list
    unique_values = list(set(split_values))

    return unique_values


@login_required
def permission_menu(request, username):
    # print("function working")
    # print(username)
    obj = User.objects.get(username=username)
    # print(obj.last_name)
    psk_id = obj.last_name
    # print(f"username: {username}")
    user_role = get_user_role_value(request, psk_id)
    # print(user_role)
    user_role_privilege_id = get_roles_master_tbl(request, user_role)
    menus_ids = get_user_privilege_tbl(request, user_role_privilege_id)
    menus_list = get_menu_elements_tbl(request, menus_ids)

    # user_menu_obj = UserProfile.objects.get(user=obj.id)
    # print(user_menu_obj.studio_menus.all())

    user_profile, created = UserProfile.objects.get_or_create(user=obj)

    if created:
        print(f"Created new UserProfile for user with id {obj.id}.")
    else:
        print(f"Fetched existing UserProfile for user with id {obj.id}.")

    # Fetch the StudioMenus instances that match the UIDs in the menus_list
    menu_objects = StudioMenus.objects.filter(psk_id__in=menus_list)

    # Update the ManyToManyField with the new set of menu objects
    user_profile.studio_menus.set(menu_objects)


def user_login(request):
    captcha_text = generate_captcha_text()
    print(captcha_text)
    # file_name = f"{uuid.uuid4().hex}.png"  # Unique file name for each CAPTCHA
    # captcha_img = create_captcha_image(captcha_text, file_name)
    # print(f"{settings.MEDIA_URL}{captcha_img}")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user_name = form.cleaned_data['username']
            password = form.cleaned_data['password']
            md5_hash = hashlib.md5(password.encode()).hexdigest()
            captcha_text_input = request.POST.get('captcha_text_input', '')
            correct_captcha = request.POST.get('captcha_text', '')  # G

            if captcha_text_input != correct_captcha:
                messages.error(request, "Invalid CAPTCHA. Please try again.")
                return redirect('user_login')

            if user_name == "admin":
                print("username", user_name)
                user = auth.authenticate(username=user_name, password=password)
                if user is not None:
                    auth.login(request, user)
                    user_id = user.id  # Get the user ID
                    return redirect('list_menus', user_id=user_id)  # Pass user_id here

            try:
                user = User.objects.get(username=user_name)
            except User.DoesNotExist:
                user = None

            if user and user.password == md5_hash:

                if user is not None:
                    auth.login(request, user)
                    username = user.username
                    user_id = user.id  # Get the user ID

                    if user.is_staff:
                        if username == "admin":
                            return redirect('list_menus', user_id=user_id)  # Pass user_id here
                        else:
                            messages.error(request, message="Invalid username or password")
                    else:
                        permission_menu(request, username)
                        return redirect('list_menus', user_id=user_id)

            else:
                messages.error(request, message='Invalid username or password')

    # return render(request, 'login/auth_login.html')
    # context = {"captcha_text": captcha_text,  "captcha_img": f"{settings.MEDIA_URL}{captcha_img}"}
    context = {"captcha_text": captcha_text}
    return render(request, 'new_login/auth-login-cover.html', context)


def get_roles_tbl_filter(request, role_id):
    url = f"{API_STUDIO_URL}getapi/asa0501_01_01"

    payload = json.dumps({
        "queries": [
            {
                "field": "psk_id",
                "value": role_id,
                "operation": "equal"
            }
        ],
        "search_type": "first"
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = req.request("POST", url, headers=headers, data=payload)
    return response.json()


def get_roles_tbl_all(request):
    url = f"{API_STUDIO_URL}getapi/asa0501_01_01/all"
    payload = {}
    headers = {}
    response = req.request("GET", url, headers=headers, data=payload)
    return response.json()


def get_home_page_url(request):
    print("working get_home_page_url")
    get_settings_data = get_settings(request)
    # print("get_settings_data", get_settings_data)
    home_page_url = get_settings_data.get('home_page_url')
    # return redirect('home_page', home_page_url)
    return redirect('home_page')


# @login_required
# def home_page(request, home_page_url):
#     if request.user.is_superuser or request.user.first_name == "admin":
#         menus = StudioMenus.objects.filter(active=True).order_by('menu_order')
#     else:
#         user_profile = UserProfile.objects.get(user=request.user)
#         # studio_menus = user_profile.studio_menus.all()
#         menus = user_profile.studio_menus.filter(active=True).order_by('menu_order')
#
#     if request.user.is_superuser or request.user.first_name == "admin":
#         get_roles_tbl_all_data = get_roles_tbl_all(request)
#         our_rol_dashboard = []
#         our_rol_dashboard_urls = []
#         for role_id in get_roles_tbl_all_data:
#             role_id_in_value = get_roles_tbl_filter(request, role_id['psk_id'])
#
#             our_rol_dashboard.append(role_id_in_value)
#             our_rol_dashboard_urls.append(role_id_in_value['user_dashboard_url'])
#     else:
#         user_credential = get_user_data(request, request.user.username)
#
#         user_roles = user_credential['user_roles']
#
#         li_user_roles = ast.literal_eval(user_roles)
#
#         our_rol_dashboard = []
#         our_rol_dashboard_urls = []
#
#         for role_id in li_user_roles:
#             role_id_in_value = get_roles_tbl_filter(request, role_id)
#
#             our_rol_dashboard.append(role_id_in_value)
#             our_rol_dashboard_urls.append(role_id_in_value['user_dashboard_url'])
#
#     context = {
#         "active_menu_uid": 00,
#         "load_page_url": home_page_url,
#         "home_page_url": home_page_url,
#         "user_id": request.user.id,
#         "menus": menus,
#         "child_menus": menus,
#         "our_rol_dashboard": our_rol_dashboard,
#         "our_rol_dashboard_urls": our_rol_dashboard_urls,
#         "dash": True
#
#     }
#     return render(request, 'home_page.html', context)
#

@login_required
def home_page(request):
    get_settings_data = get_settings(request)
    # print("get_settings_data", get_settings_data)
    home_page_url = get_settings_data.get('home_page_url')

    if request.user.is_superuser or request.user.first_name == "admin":
        menus = StudioMenus.objects.filter(active=True).order_by('menu_order')
    else:
        user_profile = UserProfile.objects.get(user=request.user)
        menus = user_profile.studio_menus.filter(active=True).order_by('menu_order')

    # Get the first "dash" menu as a fallback
    first_dash_menu = menus.filter(menu_type="dash").first()

    if not home_page_url:
        # if first_dash_menu:
        menus = menus.exclude(id=first_dash_menu.id)

    if request.user.is_superuser or request.user.first_name == "admin":
        get_roles_tbl_all_data = get_roles_tbl_all(request)
        our_rol_dashboard = []
        our_rol_dashboard_urls = []
        for role_id in get_roles_tbl_all_data:
            role_id_in_value = get_roles_tbl_filter(request, role_id['psk_id'])

            our_rol_dashboard.append(role_id_in_value)

            # Use .get() method to safely access the key
            user_dashboard_url = role_id_in_value.get('user_dashboard_url', None)
            our_rol_dashboard_urls.append(user_dashboard_url)
    else:
        user_credential = get_user_data(request, request.user.username)

        user_roles = user_credential['user_roles']
        li_user_roles = ast.literal_eval(user_roles)

        our_rol_dashboard = []
        our_rol_dashboard_urls = []

        for role_id in li_user_roles:
            role_id_in_value = get_roles_tbl_filter(request, role_id)

            our_rol_dashboard.append(role_id_in_value)

            # Use .get() method to safely access the key
            user_dashboard_url = role_id_in_value.get('user_dashboard_url', None)
            our_rol_dashboard_urls.append(user_dashboard_url)

    context = {"first_dash_menu": first_dash_menu,"load_page_url": home_page_url, "home_page_url": home_page_url,
               "user_id": request.user.id, "menus": menus, "child_menus": menus, "our_rol_dashboard": our_rol_dashboard,
               "our_rol_dashboard_urls": our_rol_dashboard_urls, "dash": True, 'active_menu_uid': 'home'}

    return render(request, 'home_page.html', context)


@login_required
def list_menus(request, user_id):
    # settings_data_value = settings_data(request)
    # print(str(settings_data_value))
    # hm_url = settings_data_value['home_page_url']
    return redirect('home_page')


@login_required
def menu_iframe_view(request, psk_id: int):
    obj = StudioMenus.objects.get(psk_id=psk_id)

    if request.user.is_superuser or request.user.first_name == "admin":
        menus = StudioMenus.objects.all().order_by('menu_order')
    else:
        user_profile = UserProfile.objects.get(user=request.user)
        menus = user_profile.studio_menus.filter(active=True).order_by('menu_order')

    context = {
        "user_id": request.user.id,
        "obj": obj,
        "child_menus": menus,
        "menus": menus,
        "active_menu_uid": obj.psk_id

    }

    return render(request, 'iframe_view.html', context)


@login_required
def user_menus(request, user_id):
    context = {"user_id": user_id}
    return render(request, 'login/user_menus.html', context)


@login_required
def get_user_data(request, username):
    url = f"{API_STUDIO_URL}getapi/asa0504_01_01"

    payload = json.dumps({
        "queries": [
            {
                "field": "username",
                "value": username,
                "operation": "equal"
            }
        ],
        "search_type": "first"
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = req.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        result = response.json()
    else:
        result = 404

    return result


@login_required
def user_profile(request):
    create_user_config = True if CREATE_USER == "True" else False
    username = request.user.username

    if username == "admin":
        messages.success(request, message="Admin users cannot update their profile picture.")
        return redirect("list_menus", request.user.id)

    user_data = get_user_data(request, username)

    photo_url = fetch_user_photo(request)

    if user_data == 404:
        messages.error(request, message="Get Api Not Working, 'asa0504_01_01'")

    if request.user.is_superuser or request.user.first_name == "admin":
        menus = StudioMenus.objects.all().order_by('menu_order')
    else:
        user_profile = UserProfile.objects.get(user=request.user)
        menus = user_profile.studio_menus.filter(active=True).order_by('menu_order')

    context = {
        "user_id": request.user.id,
        "create_user_config": create_user_config,
        "child_menus": menus,
        "menus": menus,
        "user_data": user_data, "photo_url": photo_url}
    return render(request, 'login/profile_form.html', context)


@login_required
def profile_pic_update(request, user_id, psk_id):
    # print(user_type, username, psk_id)
    # print("function working", psk_id)
    _id_url = f"{API_STUDIO_URL}crudapp/get/media/asa0504_01_01_media/parent/{psk_id}"

    payload = {}
    headers = {
        'Content-Type': 'application/json'
    }

    response = req.request("GET", _id_url, headers=headers, data=payload)
    # print(response.text)

    if response.text == "[]":
        # print("first time picture update")
        if request.method == 'POST':
            profile_photo = request.FILES.get('upload_photo')
            url = f"{API_STUDIO_URL}crudapp/upload/media/asa0504_01_01_media"

            payload = {'parent_psk_id': psk_id}
            files = [
                ('media',
                 (profile_photo.name, profile_photo.read(), 'image/png'))
            ]
            # print(files)
            headers = {}

            response = req.request("POST", url, headers=headers, data=payload, files=files)
            if response.status_code == 200:
                messages.success(request, message=f"profile photo was updated successfully.")
                return redirect('list_menus', user_id)
            else:
                error_res = response.json()
                messages.error(request, message=f"{error_res['detail']}")
                return redirect('list_menus', user_id)

    else:
        # print("update")
        user_data = response.json()[0]

        if request.method == 'POST':
            profile_photo = request.FILES.get('upload_photo')
            url = f"{API_STUDIO_URL}crudapp/upload/media/asa0504_01_01_media/{user_data['psk_id']}"

            payload = {'parent_psk_id': psk_id}
            files = [
                ('media',
                 (profile_photo.name, profile_photo.read(), 'image/png'))
            ]
            headers = {}

            response = req.request("PUT", url, headers=headers, data=payload, files=files)
            if response.status_code == 200:
                messages.success(request, message=f"profile photo was updated successfully.")
                return redirect('list_menus', user_id)
            else:
                error_res = response.json()
                messages.error(request, message=f"{error_res['detail']}")
                return redirect('list_menus', user_id)


@login_required
def profile_form_update(request, user_id):
    username = request.user.username
    response = get_user_data(request, username)
    if response == 404:
        messages.error(request, message="Get Api Not Working, 'asa0504_01_01'")

    user_data = response
    print(user_data)

    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        usertype = user_data['user_type']
        email = request.POST['email']
        userrole = user_data['user_roles']
        reporting = user_data['reporting_to']

        update_user_api_url = f"{API_STUDIO_URL}updateapi/update/asa0504_01_01/{user_data['psk_id']}"

        payload = json.dumps({
            "data": {
                "username": user_data['username'],
                "user_type": usertype.title(),
                "first_name": first_name,
                "email": email,
                "reporting_to": reporting,
                "user_roles": userrole,
                "password": user_data['password'],
                "last_name": last_name,
                "home_menu": ""
            }
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = req.request("PUT", update_user_api_url, headers=headers, data=payload)

        if response.status_code == 200:
            messages.success(request, message=f"The user '{user_data['username']}' was updated successfully.")
            return redirect('list_menus', user_id)
        else:
            error_res = response.json()
            messages.error(request, message=f"{error_res['detail']}")


@login_required
def reset_password(request, user_id):
    username = request.user.username

    if request.method == 'POST':
        password = request.POST['password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if request.user.is_superuser:
            user = request.user

            if user.check_password(password):
                # Password is correct, now check if the new passwords match
                if new_password == confirm_password:
                    user.set_password(new_password)  # Set the new password
                    user.save()  # Save the changes to the dat
                messages.success(request, message="Admin password updated successfully.")
                return redirect('list_menus', user_id=user_id)

        md5_hash = hashlib.md5(password.encode()).hexdigest()
        response = get_user_data(request, username)
        if response == 404:
            messages.error(request, message="Get Api Not Working, 'asa0504_01_01'")

        user_data = response
        psk_id = user_data['psk_id']

        if user_data['password'] != md5_hash:
            messages.error(request, message="Current password wrong")
            return redirect('list_menus', user_id)

        if new_password != confirm_password:
            messages.error(request, message="New password and confirm password do not match.")
            return redirect('list_menus', user_id)

        firstname = user_data['first_name']
        usertype = user_data['user_type']
        email = user_data['email']
        userrole = user_data['user_roles']
        reporting = user_data['reporting_to']

        new_pass_hashed_value = hashlib.md5(new_password.encode()).hexdigest()

        obj = User.objects.get(last_name=psk_id)
        obj.password = new_pass_hashed_value
        obj.save()

        update_user_api_url = f"{API_STUDIO_URL}updateapi/update/asa0504_01_01/{user_data['psk_id']}"

        payload = json.dumps({
            "data": {
                "username": user_data['username'],
                "user_type": usertype,
                "first_name": firstname,
                "email": email,
                "reporting_to": reporting,
                "user_roles": userrole,
                "password": new_pass_hashed_value,
                "last_name": user_data['last_name'],
                "home_menu": None
            }
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = req.request("PUT", update_user_api_url, headers=headers, data=payload)

        if response.status_code == 200:
            messages.success(request, message=f" password updated successfully.")
            return redirect('list_menus', user_id=user_id)
        else:
            error_res = response.json()
            messages.error(request, message=f"{error_res['detail']}")
            return redirect('list_menus', user_id=user_id)


@login_required
def fetch_user_photo(request):
    username = request.user.username
    response = get_user_data(request, username)
    if response == 404:
        photo_url = None
        return photo_url

    user_data = response
    # print(user_data)

    photo_tbl_url = f"{API_STUDIO_URL}crudapp/get/media/asa0504_01_01_media/parent/{user_data['psk_id']}"

    photo_response = req.request("GET", photo_tbl_url, headers={})

    photo_response_data = photo_response.json()
    if photo_response_data:
        photo_response_value = photo_response_data[0]
        photo_url = f"{API_STUDIO_URL}crudapp/view/media/asa0504_01_01_media/{photo_response_value['psk_id']}"
    else:
        photo_url = None

    return photo_url


@login_required
def fetch_user_obj(request, user_id):
    # print("function working")
    user_data_url = f"{API_STUDIO_URL}sqlviews/api/v1/get_respone_data/"

    payload = json.dumps({
        "psk_uid": "e02e7946-e732-418d-8a88-c13105cf4696",
        "project": "public",
        "data": {
            "psk_id": user_id
        }
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = req.request("POST", user_data_url, headers=headers, data=payload)
    fetch_user_obj_value = response.json()[0]
    if response.status_code != 200:
        messages.error(request, message="Sql Views Api request failed")

    return fetch_user_obj_value


def reset_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # print(email)

        try:
            user = User.objects.get(email=email)

            if user:
                # Generate a random token
                reset_token = secrets.token_urlsafe(16)

                # Set expiration time (2 minutes from now)
                expiration_time = datetime.utcnow() + timedelta(minutes=30)

                # JWT encoding
                payload = {
                    "sub": user.id,
                    "name": user.username,
                    "iat": int(time.time()),
                    "exp": expiration_time,  # Add the expiration time to the payload
                    "reset_token": reset_token
                }
                secret = "Ravipass"
                encoded_jwt = jwt.encode(payload, secret, algorithm='HS256')

                # Fetching access token for API Studio
                url = f"{API_STUDIO_URL}auth/token?secret_key=jzXCKtnwRMVoxhCegjLEIFDeXKO5AXzb"
                payload = json.dumps({
                    "secret_key": "jzXCKtnwRMVoxhCegjLEIFDeXKO5AXzb"
                })
                headers = {
                    'Content-Type': 'application/json'
                }

                response = req.post(url, headers=headers, data=payload)
                # print(response.text)

                if response.status_code == 200:
                    response_data = response.json()
                    access_token = response_data.get("access_token")

                    if access_token:

                        update_url = f"{API_STUDIO_URL}postapi/create/api_studio_app_password_reset_tokens"
                        update_payload = json.dumps({
                            "data": {
                                "token": encoded_jwt,
                                "token_expiry": 30,  # Example expiry time in minutes
                                "username": user.username,
                                "used": False
                            }
                        })
                        update_headers = {
                            'Content-Type': 'application/json'
                        }

                        update_response = req.post(update_url, headers=update_headers, data=update_payload)
                        # print(update_response.text)

                        # Send password reset email

                        if update_response.status_code == 200:
                            res_data = update_response.json()
                            psk_id = res_data['psk_id']

                            url = f"{API_STUDIO_URL}coreapi/api/asa01101"
                            payload = json.dumps({
                                "data": {
                                    "email": email,
                                    "link": f"{PYKIT_URL}/confirm_password/{encoded_jwt}/{psk_id}/",
                                    "username": user.username
                                }
                            })
                            headers = {
                                'Content-Type': 'application/json',
                                'Authorization': f'Bearer {access_token}'
                            }

                            response = req.post(url, headers=headers, data=payload)

                            if response.status_code == 200:
                                # Redirect to a success page
                                messages.success(request, "Password reset link sent successfully through email.")
                                return redirect('user_login')
                            else:
                                # Handle API error for token update
                                return render(request, 'reset_password/forgotpassword.html',
                                              {'error': 'Failed to update token information. Please try again.'})
                        else:
                            # Handle API error for email sending
                            return render(request, 'reset_password/forgotpassword.html',
                                          {'error': 'Failed to send reset email. Please try again.'})
                else:
                    # Handle token fetching error
                    return render(request, 'reset_password/forgotpassword.html',
                                  {'error': 'Failed to obtain access token. Please try again.'})
        except User.DoesNotExist:
            # Handle case where the user does not exist
            return render(request, 'reset_password/forgotpassword.html', {'error': 'No account found with that email.'})

    return render(request, 'reset_password/forgotpassword.html')


def confirm_password_view(request, encoded_jwt, psk_id):
    if request.method == 'POST':
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            # If passwords don't match, stay on the same page and show error
            messages.error(request, 'Passwords do not match.')
            return render(request, 'reset_password/confirm_password.html')

        try:
            # Decode JWT and validate expiration
            secret = "Ravipass"
            decoded_jwt = jwt.decode(encoded_jwt, secret, algorithms=['HS256'])

            # Extract information from the payload
            user_id = decoded_jwt.get("sub")
            reset_token = decoded_jwt.get("reset_token")

            # Fetch user
            user = User.objects.get(id=user_id)

            if user:
                # Update the user's password
                # user.set_password(new_password)
                # user.save()

                new_pass_hashed_value = hashlib.md5(new_password.encode()).hexdigest()
                user.password = new_pass_hashed_value
                user.save()

                user_psk_id = user.last_name
                us_update_url = f"{API_STUDIO_URL}updateapi/update/asa0504_01_01/{user_psk_id}"
                us_update_payload = json.dumps({
                    "data": {
                        "password": new_pass_hashed_value
                    }
                })
                us_update_headers = {
                    'Content-Type': 'application/json'
                }

                # Perform the PUT request to update the token status
                us_update_response = req.put(us_update_url, headers=us_update_headers, data=us_update_payload)
                # print(f"Update Response Status Code: {update_response.status_code}")
                # print(f"Update Response Body: {update_response.text}")

                if us_update_response.status_code != 200:
                    messages.error(request, 'User master table not update')
                    return render(request, 'reset_password/confirm_password.html')

                # Update the token's 'used' field
                update_url = f"{API_STUDIO_URL}updateapi/update/api_studio_app_password_reset_tokens/{psk_id}"
                update_payload = json.dumps({
                    "data": {
                        "used": True
                    }
                })
                update_headers = {
                    'Content-Type': 'application/json'
                }

                # Perform the PUT request to update the token status
                update_response = req.put(update_url, headers=update_headers, data=update_payload)
                # print(f"Update Response Status Code: {update_response.status_code}")
                # print(f"Update Response Body: {update_response.text}")

                if update_response.status_code == 200:
                    # After successful reset, redirect to login
                    messages.success(request, "Password has been reset successfully. You can now log in with your new "
                                              "password.")
                    return redirect('user_login')
                else:
                    # Handle API error for token update
                    messages.error(request,
                                   f'Failed to update token status. Status code: {update_response.status_code}, Response: {update_response.text}')
                    return render(request, 'reset_password/confirm_password.html')

            else:
                # User not found
                messages.error(request, 'User not found.')
                return render(request, 'reset_password/confirm_password.html')

        except jwt.ExpiredSignatureError:
            # Token has expired, display error on the same page (confirm_password.html)
            messages.error(request, 'The reset link has expired. Please request a new one.')
            return render(request, 'login/auth_login.html')

        except jwt.InvalidTokenError:
            # Invalid token error
            messages.error(request, 'Invalid token.')
            return render(request, 'reset_password/confirm_password.html')

        except User.DoesNotExist:
            # Handle user not found
            messages.error(request, 'User not found.')
            return render(request, 'reset_password/confirm_password.html')

    # If it's a GET request, just render the confirm password page
    return render(request, 'reset_password/confirm_password.html')


def sneat(request):
    api_url = f"{API_STUDIO_URL}getapi/asa0507_01_01/1"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code != 200:
        print("api not working")
    obj = response.json()

    print(obj)

    # obj = SettingsModel.objects.all()
    context = {
        "menu": "menu-settings",
        "obj": obj,
        "user_id": request.user.id
    }
    return render(request, 'login/sneat_table.html', context)

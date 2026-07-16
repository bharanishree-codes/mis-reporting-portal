import configparser
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
import requests as req
import json, hashlib
import configparser
import os

from user_management.views import fetch_user_photo
from .settings_views import user_bundle_settings

API_STUDIO_URL = user_bundle_settings()

config = configparser.ConfigParser()
config.read(os.path.join(os.getcwd(), 'config.ini'))

CREATE_USER = config['DEFAULT']['CREATE_USER']


@login_required
def user_master_screen(request, user_id):
    create_user_config = True if CREATE_USER == "True" else False

    api_url = f"{API_STUDIO_URL}getapi/asa0504_01_01/all"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code == 200:
        response_json = response.json()
    else:
        messages.error(request, message="The API is not retrieving data.")

    context = {
        "menu": "menu-usermaster",
        "response_json": response_json,
        "user_id": user_id,
        "create_user_config": create_user_config
    }
    return render(request, 'users_manage/usermaster/user_master_screen.html', context)


@login_required
def user_type_value(request):
    url = f"{API_STUDIO_URL}crudapp/tables_fields/asa0504_01_01"

    payload = {}
    headers = {}

    response = req.request("GET", url, headers=headers, data=payload)
    response_data = response.json()
    fields_value = response_data['fields']
    print(fields_value)

    choices = None

    for _user_type in fields_value:
        if _user_type['field_name'] == "user_type":
            data = json.loads(_user_type['field_select'])
            choices = data["choices"]
            break

    # print(choices)
    return choices


@login_required
def create_user_master(request, user_id):
    api_url = f"{API_STUDIO_URL}getapi/asa0504_01_01/all"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code != 200:
        messages.error(request, message="The API is not User Master Table retrieving data.")
    response_json = response.json()

    users_names_list = [user['username'] for user in response_json]

    api_url2 = f"{API_STUDIO_URL}getapi/asa0501_01_01/all"

    payload = {}
    headers = {}

    res = req.request("GET", api_url2, headers=headers, data=payload)
    if response.status_code != 200:
        messages.error(request, message="The API is not 'asa0501_01_01' Table retrieving data.")
    res_json = res.json()

    user_role_list = []
    for user_role in res_json:
        user_role_list.append({"role": user_role['user_role'], "psk_id": user_role['psk_id']})

    choices_value = user_type_value(request)
    if request.method == 'POST':
        username_data = request.POST['username']
        firstname = request.POST['firstname']
        password = request.POST['password']
        usertype = request.POST['usertype']
        email = request.POST['email']
        last_name = request.POST['last_name']
        userrole = request.POST.getlist('userrole')
        reporting = request.POST['reporting']

        # password_hashed_value = hashlib.md5(password.encode).hexdigest()

        md5_hash = hashlib.md5(password.encode()).hexdigest()

        print(md5_hash)
        print(len(md5_hash))

        if not User.objects.filter(username=username_data).exists():

            obj = User(
                username=username_data,
                password=md5_hash,
                first_name=usertype,
                email=email
            )
            # obj.set_password(password)
            obj.save()
            print(obj.password)

            crete_user_api_url = f"{API_STUDIO_URL}postapi/create/asa0504_01_01"

            payload = json.dumps({
                "data": {
                    "username": username_data,
                    "password": obj.password,
                    "user_type": usertype,
                    "first_name": firstname,
                    "email": email,
                    "reporting_to": reporting,
                    "user_roles": userrole,
                    "last_name": last_name,
                    "home_menu": None,
                    "active": True
                }
            })
            headers = {
                'Content-Type': 'application/json'
            }

            response = req.request("POST", crete_user_api_url, headers=headers, data=payload)

            if response.status_code == 200:
                res_data = response.json()
                obj.last_name = res_data['psk_id']
                obj.save()

                # menu_assign = permission_menu(request, obj.username)

                messages.success(request, message=f"The user '{username_data}' was created successfully.")
                return redirect('user_master_screen', user_id)
            else:
                error_res = response.json()
                obj.delete()
                messages.error(request, message=f"{error_res['detail']}")

        else:
            messages.error(request, message="User with this username already exists.")
    context = {
        "menu": "menu-usermaster",
        "users_names_list": users_names_list,
        "user_role_list": user_role_list,
        "user_type_choices": choices_value,
        "user_id": user_id
    }
    return render(request, 'users_manage/usermaster/create_user_form.html', context)


@login_required
def update_user_master(request, user_id, psk_id):
    add_new_btn = True if CREATE_USER == "True" else False

    api_url = f"{API_STUDIO_URL}getapi/asa0504_01_01/all"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code != 200:
        messages.error(request, message="The API is not User Master Table retrieving data.")
    response_json = response.json()

    users_names_list = [user['username'] for user in response_json]

    api_url2 = f"{API_STUDIO_URL}getapi/asa0501_01_01/all"

    payload = {}
    headers = {}

    res = req.request("GET", api_url2, headers=headers, data=payload)
    if response.status_code != 200:
        messages.error(request, message="The API is not 'asa0501_01_01' Table retrieving data.")
    res_json = res.json()
    # print(res_json)

    user_role_list = []
    for user_role in res_json:
        user_role_list.append({"role": user_role['user_role'], "psk_id": user_role['psk_id']})

    user_data_url = f"{API_STUDIO_URL}getapi/asa0504_01_01/{psk_id}"

    payload = {}
    headers = {}

    response = req.request("GET", user_data_url, headers=headers, data=payload)

    if response.status_code != 200:
        messages.error(request, message="The API is not User Master Table retrieving data.")
    user_res_json = response.json()

    current_user_roles = user_res_json['user_roles']
    print("current_user_roles", current_user_roles)

    str_without_braces = current_user_roles.strip('{}')
    # Split the string by comma to get a list of string elements
    str_list = str_without_braces.split(',')

    # Convert each string element to an integer
    current_user_roles_data = [int(x) for x in str_list]

    current_role = []

    for user_data_role in res_json:
        for urole in current_user_roles_data:
            # print(urole)
            if urole == user_data_role['psk_id']:
                current_role.append(user_data_role['psk_id'])

    choices_value = user_type_value(request)

    if request.method == 'POST':
        username_data = request.POST['username']
        firstname = request.POST['firstname']
        last_name = request.POST['last_name']
        usertype = request.POST['usertype']
        email = request.POST['email']
        userrole = request.POST.getlist('userrole')
        reporting = request.POST['reporting']
        active = request.POST['status']

        if active == "active":
            active = True
        else:
            active = False

        update_user_api_url = f"{API_STUDIO_URL}updateapi/update/asa0504_01_01/{psk_id}"

        payload = json.dumps({
            "data": {
                "username": username_data,
                "user_type": usertype,
                "first_name": firstname,
                "email": email,
                "reporting_to": reporting,
                "user_roles": userrole,
                "password": user_res_json['password'],
                "last_name": last_name,
                "home_menu": None,
                "active": active

            }
        })
        print(payload)
        headers = {
            'Content-Type': 'application/json'
        }

        response = req.request("PUT", update_user_api_url, headers=headers, data=payload)

        if response.status_code == 200:

            obj = User.objects.get(last_name=psk_id)
            obj.first_name = usertype
            obj.username = username_data
            obj.is_active = active
            obj.email = email
            obj.save()

            # menu_assign = permission_menu(request, username_data)

            messages.success(request, message=f"The user '{username_data}' was updated successfully.")
            return redirect('user_master_screen', user_id)
        else:
            error_res = response.json()
            messages.error(request, message=f"{error_res['detail']}")

    context = {
        "menu": "menu-usermaster",
        "users_names_list": users_names_list,
        "user_role_list": user_role_list,
        "obj": user_res_json,
        "current_role": current_role,
        "user_type_choices": choices_value,
        "user_id": user_id,
        "add_new_btn": add_new_btn
    }
    return render(request, 'users_manage/usermaster/update_user_form.html', context)


@login_required
def delete_user_master(request, user_id, psk_id):
    print(user_id)
    delete_user_api_url = f"{API_STUDIO_URL}deleteapi/delete/asa0504_01_01/{psk_id}"

    payload = {}
    headers = {}

    response = req.request("DELETE", delete_user_api_url, headers=headers, data=payload)

    if response.status_code == 200:
        messages.success(request, message=f"The user  was deleted successfully.")
        return redirect('user_master_screen', user_id)
    else:
        error_res = response.json()
        messages.error(request, message=f"{error_res['detail']}")

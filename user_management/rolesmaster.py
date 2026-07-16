from django.contrib import messages
from django.shortcuts import render, redirect
import requests as req
import json, hashlib

from .settings_views import user_bundle_settings

API_STUDIO_URL = user_bundle_settings()


def menu_privilege_tbl(request):
    menu_privilege_url = f"{API_STUDIO_URL}getapi/asa0503_01_01/all"

    payload = {}
    headers = {}

    menu_privilege_response = req.request("GET", menu_privilege_url, headers=headers, data=payload)
    menu_privilege_list = menu_privilege_response.json()
    if menu_privilege_response.status_code != 200:
        messages.error(request, message="The API is not retrieving data.")
    return menu_privilege_list


def role_master_screen(request, user_id):
    api_url = f"{API_STUDIO_URL}getapi/asa0501_01_01/all"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code == 200:
        response_json = response.json()
        # print(response_json)
    else:
        messages.error(request, message="The API is not retrieving data.")

    menu_privilege_tbl_data = menu_privilege_tbl(request)
    # print(menu_privilege_tbl_data)
    # print(response_json)

    privilege_mapping = {str(item['psk_id']): item['menu_privilege_name'] for item in menu_privilege_tbl_data}

    # Map user_role_privilege to their corresponding names
    for role in response_json:
        privileges = role['user_role_privilege'].split(',')
        role['user_role_privilege_names'] = ', '.join(
            [privilege_mapping.get(privilege, privilege) for privilege in privileges])

    context = {
        "menu": "menu-rolesmaster",
        "user_id": user_id,
        "response_json": response_json,
        "menu_privilege_tbl_data": menu_privilege_tbl_data,
    }
    return render(request, 'users_manage/rolesmaster/role_master_screen.html', context)


def create_role_master(request, user_id):
    api_url = f"{API_STUDIO_URL}getapi/asa0505_01_01/all"
    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    user_privileges = response.json()
    if response.status_code != 200:
        messages.error(request, message="The API is not retrieving data.")
    menu_privilege_tbl_data = menu_privilege_tbl(request)

    if request.method == "POST":
        role_name = request.POST['rolename'].title()
        # dashboard_url = request.POST['dashboard_url']
        # dashboard_name = request.POST['dashboard_name']
        userpri = request.POST.getlist('userpri')

        int_list = [int(num) for num in userpri]

        userpri_list = ','.join(map(str, int_list))

        create_role_api_url = f"{API_STUDIO_URL}postapi/create/asa0501_01_01"

        payload = json.dumps({
            "data": {
                "user_role": role_name,
                "active": "Active",
                "user_role_privilege": userpri_list,
                # "user_dashboard_url": dashboard_url,
                # "user_dashboard_name": dashboard_name,
            }
        })

        headers = {
            'Content-Type': 'application/json'
        }

        response = req.request("POST", create_role_api_url, headers=headers, data=payload)

        if response.status_code == 200:
            messages.success(request, message=f"The '{role_name}' was created successfully.")
            return redirect('role_master_screen', user_id)
        else:
            error_res = response.json()
            messages.error(request, message=f"{error_res['detail']}")

    context = {
        "menu": "menu-rolesmaster",
        "user_id": user_id,
        "user_privileges": user_privileges,
        "menu_privilege_tbl_data": menu_privilege_tbl_data
    }
    return render(request, 'users_manage/rolesmaster/create_role_master.html', context)


def update_role_master(request, user_id, psk_id):
    api_url = f"{API_STUDIO_URL}getapi/asa0505_01_01/all"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    user_privileges = response.json()
    # print(user_privileges)
    if response.status_code != 200:
        messages.error(request, message="The API is not retrieving data.")

    menu_privilege_tbl_data = menu_privilege_tbl(request)
    # print(menu_privilege_tbl_data)

    click_user_privileges = []

    for menupri in menu_privilege_tbl_data:
        for userpri in user_privileges:
            if menupri['psk_id'] == int(userpri['menu_privilege']):
                click_user_privileges.append(menupri)
    # print(click_user_privileges)

    role_data_url = f"{API_STUDIO_URL}getapi/asa0501_01_01/{psk_id}"

    payload = {}
    headers = {}

    response = req.request("GET", role_data_url, headers=headers, data=payload)

    if response.status_code != 200:
        messages.error(request, message="The API is not User Master Table retrieving data.")
    role_res_json = response.json()
    comma_separated_string = role_res_json['user_role_privilege']

    # Convert the string to a list of integers
    user_privi_list = [int(num) for num in comma_separated_string.split(',')]

    if request.method == "POST":
        role_name = request.POST['rolename'].title()
        # dashboard_url = request.POST['dashboard_url']
        # dashboard_name = request.POST['dashboard_name']
        status = request.POST['status']
        userpri = request.POST.getlist('userpri')

        int_list = [int(num) for num in userpri if num.isdigit()]

        # Convert the list of integers to a comma-separated string
        userpri_list = ','.join(map(str, int_list))

        update_role_api_url = f"{API_STUDIO_URL}updateapi/update/asa0501_01_01/{psk_id}"

        payload = json.dumps({
            "data": {
                "user_role": role_name,
                "active": status,
                "user_role_privilege": userpri_list,
                # "user_dashboard_url": dashboard_url,
                # "user_dashboard_name": dashboard_name,
            }
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = req.request("PUT", update_role_api_url, headers=headers, data=payload)

        if response.status_code == 200:
            messages.success(request, message=f"The '{role_name}' was updated successfully.")
            return redirect('role_master_screen', user_id)
        else:
            error_res = response.json()
            messages.error(request, message=f"{error_res['detail']}")

    context = {
        "menu": "menu-rolesmaster",
        "user_id": user_id,
        "click_user_privileges": click_user_privileges,
        "obj": role_res_json,
        "user_privi_list": user_privi_list,
    }
    return render(request, 'users_manage/rolesmaster/update_role_master.html', context)


def delete_role_master(request, user_id, psk_id):
    delete_user_api_url = f"{API_STUDIO_URL}deleteapi/delete/asa0501_01_01/{psk_id}"

    payload = {}
    headers = {}

    response = req.request("DELETE", delete_user_api_url, headers=headers, data=payload)

    if response.status_code == 200:
        messages.success(request, message=f"The role  was deleted successfully.")
        return redirect('role_master_screen', user_id)
    else:
        error_res = response.json()
        messages.error(request, message=f"{error_res['detail']}")

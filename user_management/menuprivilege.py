from django.contrib import messages
from django.shortcuts import render, redirect
import hashlib
import requests as req
import json

from .settings_views import user_bundle_settings

API_STUDIO_URL = user_bundle_settings()


def menu_privilege_screen(request, user_id):
    api_url = f"{API_STUDIO_URL}getapi/asa0503_01_01/all"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code == 200:
        response_json = response.json()
    else:
        messages.error(request, message="The API is not retrieving data.")

    context = {
        "menu": "menu-menuprivilege",
        "response_json": response_json,
        "user_id": user_id
    }
    return render(request, 'users_manage/menu_privilege/menu_privilege_screen.html', context)


def create_menu_privilege(request, user_id):
    if request.method == 'POST':
        menu_privilege_name = request.POST['menu_privilege_name'].title()
        # active = request.POST['active']
        menu_privilege_start_date = request.POST['start_date']
        menu_privilege_end_date = request.POST['end_date']

        crete_menupriviliege_api_url = f"{API_STUDIO_URL}postapi/create/asa0503_01_01"

        payload = json.dumps({
            "data": {
                "menu_privilege_name": menu_privilege_name,
                "active": "Active",
                "menu_privilege_start_date": menu_privilege_start_date,
                "menu_privilege_end_date": menu_privilege_end_date,

            }
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = req.request("POST", crete_menupriviliege_api_url, headers=headers, data=payload)

        if response.status_code == 200:
            messages.success(request, message=f"The '{menu_privilege_name}' was created successfully.")
            return redirect('menu_privilege_screen', user_id)
        else:
            error_res = response.json()
            messages.error(request, message=f"{error_res['detail']}")

    context = {
        "menu": "menu-menuprivilege",
        "user_id": user_id,
    }
    return render(request, 'users_manage/menu_privilege/create_menu_privilege.html', context)


def update_menu_privilege(request, user_id, psk_id):
    api_url = f"{API_STUDIO_URL}getapi/asa0503_01_01/{psk_id}"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code != 200:
        messages.error(request, message="The API is not User Master Table retrieving data.")
    response_json = response.json()

    if request.method == 'POST':
        menu_privilege_name = request.POST['menu_privilege_name'].title()
        active = request.POST['active']
        menu_privilege_start_date = request.POST['start_date']
        menu_privilege_end_date = request.POST['end_date']

        update_menupriviliege_api_url = f"{API_STUDIO_URL}updateapi/update/asa0503_01_01/{psk_id}"

        payload = json.dumps({
            "data": {
                "menu_privilege_name": menu_privilege_name,
                "active": active,
                "menu_privilege_start_date": menu_privilege_start_date,
                "menu_privilege_end_date": menu_privilege_end_date,

            }
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = req.request("PUT", update_menupriviliege_api_url, headers=headers, data=payload)

        if response.status_code == 200:
            messages.success(request, message=f"The '{menu_privilege_name}' was updated successfully.")
            return redirect('menu_privilege_screen', user_id)
        else:
            error_res = response.json()
            messages.error(request, message=f"{error_res['detail']}")

    context = {
        "menu": "menu-menuprivilege",
        "user_id": user_id,
        "obj": response_json,
    }
    return render(request, 'users_manage/menu_privilege/update_menu_privilege.html', context)


def delete_menu_privilege(request, user_id, psk_id):
    delete_user_api_url = f"{API_STUDIO_URL}deleteapi/delete/asa0503_01_01/{psk_id}"

    payload = {}
    headers = {}

    response = req.request("DELETE", delete_user_api_url, headers=headers, data=payload)

    if response.status_code == 200:
        messages.success(request, message=f"The privilege  was deleted successfully.")
        return redirect('menu_privilege_screen', user_id)
    else:
        error_res = response.json()
        messages.error(request, message=f"{error_res['detail']}")







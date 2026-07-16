from django.contrib import messages
from django.shortcuts import render, redirect
import requests as req
import json
from .models import *

from .settings_views import user_bundle_settings

API_STUDIO_URL = user_bundle_settings()


def menu_elements_screen(request, user_id):
    api_url = f"{API_STUDIO_URL}getapi/asa0502_01_01/all"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code == 200:
        response_json = response.json()

    else:
        messages.error(request, message="The API is not retrieving data.")

    context = {
        "menu": "menu-menuelements",
        "response_json": response_json,
        "user_id": user_id,
    }

    return render(request, 'users_manage/menu_elements/menu_elements_screen.html', context)


def drop_down_menu_get():
    api_url = f"{API_STUDIO_URL}getapi/asa0502_01_01"
    payload = json.dumps({
        "queries": [

            {
                "field": "menu_type",
                "value": "dropdown",
                "operation": "equal"
            },

        ],
        "search_type": "all"
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = req.request("POST", api_url, headers=headers, data=payload)
    if response.status_code == 200:
        phc_data = response.json()
    else:
        phc_data = []

    return phc_data


def create_menu_element(request, user_id):
    # menu_lists_data = f"{API_STUDIO_URL}getapi/asa0502_01_01/all"
    #
    # payload = {}
    # headers = {}
    #
    # response = req.request("GET", menu_lists_data, headers=headers, data=payload)
    # menus_name_list = response.json()
    # print(menus_name_list)

    menus_name_list = drop_down_menu_get()

    # if response.status_code != 200:
    #     messages.error(request, message="The API is not retrieving data.")

    if request.method == "POST":
        menu_view = request.POST['menu_view']
        menu_name = request.POST['menu_name'].title()
        menu_type = request.POST['menu_type']
        href_value = request.POST['href_value']
        parent_id = request.POST['parent_id']
        icon_value = request.POST['icon_value']
        menu_unique_id = request.POST['menu_unique_id']
        menu_order = request.POST['menu_order']
        active = "Active"
        menu_code = request.POST['menu_code']

        # Create the menu element via API
        create_role_api_url = f"{API_STUDIO_URL}postapi/create/asa0502_01_01"
        payload = json.dumps({
            "data": {
                "menu_app_bar": menu_view,
                "menu_href": href_value,
                "menu_icon": icon_value,
                "menu_name": menu_name,
                "menu_order": menu_order,
                "menu_type": menu_type,
                "menu_uid": menu_unique_id,
                "menu_parent_id": parent_id,
                "active": active,
                "menu_psk_uid": "0",
                "menu_level": "0",
                "menu_psk_id": "1",
                "menu_code": menu_code,
            }
        })
        headers = {'Content-Type': 'application/json'}
        response = req.request("POST", create_role_api_url, headers=headers, data=payload)

        # Save the menu element in the Django database
        if response.status_code == 200:
            res_data = response.json()
            StudioMenus.objects.create(
                menu_name=menu_name,
                menu_uid=menu_unique_id,
                menu_href=href_value,
                icon_class=icon_value,
                menu_ui_code=menu_view,
                active=True if active == "Active" else False,
                menu_order=menu_order,
                menu_app_bar=menu_view,
                menu_code=menu_code,
                menu_parent_id=parent_id,
                psk_id=res_data['psk_id'],
                menu_type=menu_type,
            )
            messages.success(request, message=f"The '{menu_name}' was created successfully.")
            return redirect('menu_elements_screen', user_id)
        else:
            error_res = response.json()
            messages.error(request, message=f"{error_res['detail']}")

    context = {
        "menu": "menu-menuelements",
        "user_id": user_id,
        "menu_lists_data": menus_name_list,
    }
    # return render(request, 'users_manage/menu_elements/create_menu_element.html', context)
    return render(request, 'users_manage/menu_elements/create_menu_element-rnd.html', context)


def update_menu_element(request, user_id, psk_id):
    # menu_lists_data = f"{API_STUDIO_URL}getapi/asa0502_01_01/all"
    # headers = {}
    #
    # # Fetch all menu names
    # response = req.request("GET", menu_lists_data, headers=headers)
    #
    # if response.status_code != 200:
    #     messages.error(request, "The API is not retrieving data.")
    #
    # menus_name_list = response.json()

    menus_name_list = drop_down_menu_get()
    # Filter out dictionaries with the specified psk_id
    filtered_menus = [menu for menu in menus_name_list if menu.get('psk_id') != psk_id]

    # Fetch existing menu element by ID
    id_against_url = f"{API_STUDIO_URL}getapi/asa0502_01_01/{psk_id}"
    headers = {}
    response = req.request("GET", id_against_url, headers=headers)
    if response.status_code != 200:
        messages.error(request, "The API is not retrieving data.")
    id_base_data = response.json()

    if request.method == "POST":
        menu_view = request.POST['menu_view']
        menu_name = request.POST['menu_name'].title()
        menu_type = request.POST['menu_type']
        href_value = request.POST['href_value']
        parent_id = request.POST['parent_id']
        icon_value = request.POST['icon_value']
        menu_unique_id = request.POST['menu_unique_id']
        menu_order = int(request.POST['menu_order'])
        active = request.POST.get('active', "Active")  # Ensure default to "Active" if not set
        menu_code = request.POST['menu_code']

        update_menu_api_url = f"{API_STUDIO_URL}updateapi/update/asa0502_01_01/{psk_id}"
        payload = json.dumps({
            "data": {
                "menu_app_bar": menu_view,
                "menu_href": href_value,
                "menu_icon": icon_value,
                "menu_name": menu_name,
                "menu_order": menu_order,
                "menu_type": menu_type,
                "menu_uid": menu_unique_id,
                "menu_parent_id": parent_id,
                "active": active,
                "menu_psk_uid": "0",
                "menu_level": "0",
                "menu_psk_id": "1",
                "menu_code": menu_code,
            }
        })
        headers = {'Content-Type': 'application/json'}
        response = req.request("PUT", update_menu_api_url, headers=headers, data=payload)

        if response.status_code == 200:
            res_data = response.json()
            # Update the record in Django admin
            StudioMenus.objects.filter(psk_id=res_data['psk_id']).update(
                menu_name=menu_name,
                menu_uid=menu_unique_id,
                menu_href=href_value,
                icon_class=icon_value,
                menu_ui_code=menu_view,
                active=(active == "Active"),
                menu_order=menu_order,
                menu_app_bar=menu_view,
                menu_code=menu_code,
                menu_parent_id=parent_id,
                menu_type=menu_type,

            )

            messages.success(request, f"The '{menu_name}' was updated successfully.")
            return redirect('menu_elements_screen', user_id)
        else:
            error_res = response.json()
            messages.error(request, f"{error_res.get('detail', 'Error updating menu element')}")

    context = {
        "menu": "menu-menuelements",
        "user_id": user_id,
        "menu_lists_data": filtered_menus,
        "obj": id_base_data
    }
    # return render(request, 'users_manage/menu_elements/update_menu_element.html', context)
    return render(request, 'users_manage/menu_elements/update_menu_element.html', context)


def delete_menu_element(request, user_id, psk_id):
    delete_user_api_url = f"{API_STUDIO_URL}deleteapi/delete/asa0502_01_01/{psk_id}"

    payload = {}
    headers = {}

    response = req.request("DELETE", delete_user_api_url, headers=headers, data=payload)
    print(delete_user_api_url)
    print(psk_id)
    print(response.text)

    if response.status_code == 200:
        StudioMenus.objects.filter(psk_id=psk_id).delete()

        messages.success(request, message=f"The menu  was deleted successfully.")
        return redirect('menu_elements_screen', user_id)
    else:
        error_res = response.json()
        messages.error(request, message=f"{error_res['detail']}")


def menus_get_insert(request):
    api_url = f"{API_STUDIO_URL}getapi/asa0502_01_01/all"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code == 200:
        response_json = response.json()
        for menu in response_json:
            StudioMenus.objects.create(
                psk_id=menu['psk_id'],
                menu_name=menu['menu_name'],
                menu_uid=menu['menu_uid'],
                menu_href=menu['menu_href'] or '',  # Ensure empty href is properly inserted
                menu_ui_code=menu.get('menu_ui_code', ''),  # Default empty string if menu_ui_code is missing
                icon_class=menu['menu_icon'],
                active=True if menu['active'] == 'Active' else False,
                menu_app_bar=menu['menu_app_bar'] or '',  # Ensure empty app_bar value is inserted
                menu_order=menu['menu_order'],
                menu_code=menu['menu_code'] or '',  # Ensure menu_code is set if empty
                menu_type=menu['menu_type'],
                menu_parent_id=menu['menu_parent_id'],
            )

        print(response_json)
        return redirect('user_login')
    else:
        messages.error(request, message="The API is not retrieving data.")
        return None

from django.contrib import messages
from django.shortcuts import render, redirect
import requests as req
import json

from .settings_views import user_bundle_settings

API_STUDIO_URL = user_bundle_settings()


# def user_privilege_screen(request, user_id):
#     api_url = f"{API_STUDIO_URL}getapi/asa0505_01_01/all"
#     payload = {}
#     headers = {}
#
#     # Fetch all user privileges
#     response = req.request("GET", api_url, headers=headers, data=payload)
#     if response.status_code == 200:
#         response_json = response.json()
#     else:
#         messages.error(request, message="The API is not retrieving data.")
#
#     # Fetch all menu names
#     menu_api_url = f"{API_STUDIO_URL}getapi/asa0502_01_01/all"
#     menu_response = req.request("GET", menu_api_url, headers=headers, data=payload)
#     if menu_response.status_code == 200:
#         menus_name_list = menu_response.json()
#     else:
#         messages.error(request, message="The menu API is not retrieving data.")
#
#     # Create a mapping of menu_ids to menu_names
#     menu_id_to_name = {menu['psk_id']: menu['menu_name'] for menu in menus_name_list}
#
#     # Add the corresponding menu names to each privilege
#     for privilege in response_json:
#         # Get the comma-separated menu_ids and convert to a list of integers
#         menu_ids = privilege['menu_items'].split(',')
#         # Map the menu_ids to their respective names
#         privilege['menu_names'] = [menu_id_to_name.get(int(menu_id)) for menu_id in menu_ids]
#
#     context = {
#         "menu": "menu-userprivilege",
#         "response_json": response_json,
#         "user_id": user_id
#     }
#     return render(request, 'users_manage/userprivilege/user_privilege_screen.html', context)


def user_privilege_screen(request, user_id):
    api_url = f"{API_STUDIO_URL}getapi/asa0505_01_01/all"

    response = req.get(api_url)
    if response.status_code == 200:
        response_json = response.json()
    else:
        messages.error(request, message="The API is not retrieving data.")
        response_json = []

    menu_pre_url = f"{API_STUDIO_URL}getapi/asa0503_01_01/all"

    menu_pre_response = req.get(menu_pre_url)
    if response.status_code == 200:
        menu_pre_data = menu_pre_response.json()

    else:
        messages.error(request, message="The API is not retrieving data asa0503_01_01.")
        response_json = []

    api_url = f"{API_STUDIO_URL}getapi/asa0502_01_01/all"

    response = req.get(api_url)
    if response.status_code == 200:
        menus_name_list = response.json()
        menus_dict = {str(menu['psk_id']): menu['menu_name'] for menu in menus_name_list}
    else:
        messages.error(request, message="The API is not retrieving data.")
        menus_dict = {}

    # Process the response_json to include menu names
    for obj in response_json:
        menu_ids = obj['menu_items'].split(',')
        obj['menu_names'] = [menus_dict.get(menu_id.strip(), menu_id) for menu_id in menu_ids]

    context = {
        "menu": "menu-userprivilege",
        "menu_pre_data": menu_pre_data,
        "response_json": response_json,
        "user_id": user_id,
    }
    return render(request, 'users_manage/userprivilege/user_privilege_screen.html', context)


# def user_privilege_tbl(request):
#     api_url = f"{API_STUDIO_URL}getapi/asa0505_01_01/all"
#
#     response = req.get(api_url)
#     if response.status_code == 200:
#         response_json = response.json()
#         return response_json
#     else:
#         messages.error(request, message="The API is not retrieving data.")
#         response_json = []

def user_privilege_tbl(request):
    api_url = f"{API_STUDIO_URL}getapi/asa0505_01_01/all"

    response = req.get(api_url)
    if response.status_code == 200:
        response_json = response.json()
        return response_json
    else:
        messages.error(request, message="The API is not retrieving data.")
        response_json = []


# def create_user_privilege(request, user_id):
#     # Fetching available menus
#     api_url = f"{API_STUDIO_URL}getapi/asa0502_01_01/all"
#     response = req.request("GET", api_url)
#     menus_name_list = response.json()
#     if response.status_code != 200:
#         messages.error(request, message="The API is not retrieving data.")
#
#     # Fetching menu privileges
#     menu_privilege_url = f"{API_STUDIO_URL}getapi/asa0503_01_01/all"
#     menu_privilege_response = req.request("GET", menu_privilege_url)
#     menu_privilege_list = menu_privilege_response.json()
#     if menu_privilege_response.status_code != 200:
#         messages.error(request, message="The API is not retrieving data.")
#
#     # Getting existing user privileges
#     user_privilege_tbl_data = user_privilege_tbl(request)
#     user_privilege_menu_ids = [user_pri['menu_privilege'] for user_pri in user_privilege_tbl_data]
#
#     # Filtering unused menu privileges
#     not_use_menupri = [
#         menu_pri for menu_pri in menu_privilege_list
#         if str(menu_pri['psk_id']) not in user_privilege_menu_ids
#     ]
#
#     if request.method == "POST":
#         menu_privilege = request.POST['menupri']
#         view_menus = request.POST.getlist('view_menus')
#
#         # Convert view_menus to a comma-separated string
#         view_menus_list = ','.join(map(str, view_menus))
#
#         # Fetch the menu_privilege_name for the selected psk_id
#         selected_privilege_name = next((privilege['menu_privilege_name'] for privilege in menu_privilege_list if
#                                         privilege['psk_id'] == menu_privilege), "")
#
#         create_role_api_url = f"{API_STUDIO_URL}postapi/create/asa0505_01_01"
#         payload = json.dumps({
#             "data": {
#                 "menu_privilege": menu_privilege,  # Store psk_id
#                 "menu_items": view_menus_list,
#                 "user_privilege_name": selected_privilege_name,  # Optionally store the name
#             }
#         })
#         headers = {
#             'Content-Type': 'application/json'
#         }
#
#         response = req.request("POST", create_role_api_url, headers=headers, data=payload)
#
#         if response.status_code == 200:
#             messages.success(request, message=f"The '{selected_privilege_name}' was assigned successfully.")
#             return redirect('user_privilege_screen', user_id)
#         else:
#             error_res = response.json()
#             messages.error(request, message=f"{error_res['detail']}")
#
#     context = {
#         "menu": "menu-userprivilege",
#         "user_id": user_id,
#         "menus_name_list": menus_name_list,
#         "menu_privilege_list": not_use_menupri
#     }
#     return render(request, 'users_manage/userprivilege/create_user_privilege.html', context)


def create_user_privilege(request, user_id):
    api_url = f"{API_STUDIO_URL}getapi/asa0502_01_01/all"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    menus_name_list = response.json()
    if response.status_code != 200:
        messages.error(request, message="The API is not retrieving data.")

    menu_privilege_url = f"{API_STUDIO_URL}getapi/asa0503_01_01/all"

    payload = {}
    headers = {}

    menu_privilege_response = req.request("GET", menu_privilege_url, headers=headers, data=payload)
    menu_privilege_list = menu_privilege_response.json()
    print(menu_privilege_list)

    if menu_privilege_response.status_code != 200:
        messages.error(request, message="The API is not retrieving data.")

    user_privilege_tbl_data = user_privilege_tbl(request)

    print(user_privilege_tbl_data)

    user_privilege_menu_ids = [user_pri['menu_privilege'] for user_pri in user_privilege_tbl_data]

    not_use_menupri = []

    for menu_pri in menu_privilege_list:
        if str(menu_pri['psk_id']) not in user_privilege_menu_ids:
            not_use_menupri.append(menu_pri)

    if request.method == "POST":
        menu_privilege = request.POST['menupri']
        view_menus = request.POST.getlist('view_menus')

        int_list = [int(num) for num in view_menus]

        # Convert the list of integers to a comma-separated string
        view_menus_list = ','.join(map(str, int_list))

        create_role_api_url = f"{API_STUDIO_URL}postapi/create/asa0505_01_01"

        payload = json.dumps({
            "data": {
                "menu_privilege": menu_privilege,
                "menu_items": view_menus_list,
                "user_privilege_name": "",
            }
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = req.request("POST", create_role_api_url, headers=headers, data=payload)

        if response.status_code == 200:
            messages.success(request, message=f"The '{menu_privilege}' was menus assigned successfully.")
            return redirect('user_privilege_screen', user_id)
        else:
            error_res = response.json()
            messages.error(request, message=f"{error_res['detail']}")

    context = {
        "menu": "menu-userprivilege",
        "user_id": user_id,
        "menus_name_list": menus_name_list,
        "menu_privilege_list": not_use_menupri
    }
    return render(request, 'users_manage/userprivilege/create_user_privilege.html', context)


# def update_user_privilege(request, user_id, psk_id):
#     api_url = f"{API_STUDIO_URL}getapi/asa0502_01_01/all"
#
#     payload = {}
#     headers = {}
#
#     response = req.request("GET", api_url, headers=headers, data=payload)
#     menus_name_list = response.json()
#     if response.status_code != 200:
#         messages.error(request, message="The API is not retrieving data.")
#
#     menu_privilege_url = f"{API_STUDIO_URL}getapi/asa0503_01_01/all"
#
#     payload = {}
#     headers = {}
#
#     menu_privilege_response = req.request("GET", menu_privilege_url, headers=headers, data=payload)
#     menu_privilege_list = menu_privilege_response.json()
#     if menu_privilege_response.status_code != 200:
#         messages.error(request, message="The API is not retrieving data.")
#
#     menu_data_url = f"{API_STUDIO_URL}getapi/asa0505_01_01/{psk_id}"
#
#     payload = {}
#     headers = {}
#
#     response = req.request("GET", menu_data_url, headers=headers, data=payload)
#
#     if response.status_code != 200:
#         messages.error(request, message="The API is not User Master Table retrieving data.")
#     menu_res_json = response.json()
#     comma_separated_string = menu_res_json['menu_items']
#
#     # Convert the string to a list of integers
#     previous_menus_list = [int(num) for num in comma_separated_string.split(',')]
#
#     if request.method == "POST":
#         menu_privilege = request.POST['menupri']
#         view_menus = request.POST.getlist('view_menus')
#
#         int_list = [int(num) for num in view_menus]
#
#         # Convert the list of integers to a comma-separated string
#         view_menus_list = ','.join(map(str, int_list))
#
#         update_role_api_url = f"{API_STUDIO_URL}updateapi/update/asa0505_01_01/{psk_id}"
#
#         payload = json.dumps({
#             "data": {
#                 "menu_privilege": menu_privilege,
#                 "menu_items": view_menus_list,
#                 "user_privilege_name": "",
#             }
#         })
#         headers = {
#             'Content-Type': 'application/json'
#         }
#
#         response = req.request("PUT", update_role_api_url, headers=headers, data=payload)
#
#         if response.status_code == 200:
#             messages.success(request, message=f"The '{menu_privilege}' was menus updated successfully.")
#             return redirect('user_privilege_screen', user_id)
#         else:
#             error_res = response.json()
#             messages.error(request, message=f"{error_res['detail']}")
#
#     context = {
#         "menu": "menu-userprivilege",
#         "user_id": user_id,
#         "menus_name_list": menus_name_list,
#         "menu_privilege_list": menu_privilege_list,
#         "menu_res_json": menu_res_json,
#         "previous_menus_list": previous_menus_list
#     }
#     return render(request, 'users_manage/userprivilege/update_user_privilege.html', context)

def update_user_privilege(request, user_id, psk_id):
    # print(request.user)
    api_url = f"{API_STUDIO_URL}getapi/asa0502_01_01/all"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    menus_name_list = response.json()
    if response.status_code != 200:
        messages.error(request, message="The API is not retrieving data.")

    menu_pre_url = f"{API_STUDIO_URL}getapi/asa0503_01_01/all"
    menu_pre_response = req.get(menu_pre_url)
    if response.status_code == 200:
        menu_pre_data = menu_pre_response.json()
        print(menu_pre_data)
        # menu_pre_data = menu_pre_data['menu_privilege_name']
    else:
        messages.error(request, message="The API is not retrieving data asa0203_01_01.")



    menu_privilege_url = f"{API_STUDIO_URL}getapi/asa0503_01_01/all"

    payload = {}
    headers = {}

    menu_privilege_response = req.request("GET", menu_privilege_url, headers=headers, data=payload)
    menu_privilege_list = menu_privilege_response.json()
    if menu_privilege_response.status_code != 200:
        messages.error(request, message="The API is not retrieving data.")

    menu_data_url = f"{API_STUDIO_URL}getapi/asa0505_01_01/{psk_id}"

    payload = {}
    headers = {}

    response = req.request("GET", menu_data_url, headers=headers, data=payload)

    if response.status_code != 200:
        messages.error(request, message="The API is not User Master Table retrieving data.")
    menu_res_json = response.json()
    comma_separated_string = menu_res_json['menu_items']

    # Convert the string to a list of integers
    previous_menus_list = [int(num) for num in comma_separated_string.split(',')]

    if request.method == "POST":
        menu_privilege = request.POST['menupri']
        view_menus = request.POST.getlist('view_menus')

        int_list = [int(num) for num in view_menus]

        # Convert the list of integers to a comma-separated string
        view_menus_list = ','.join(map(str, int_list))

        update_role_api_url = f"{API_STUDIO_URL}updateapi/update/asa0505_01_01/{psk_id}"

        payload = json.dumps({
            "data": {
                "menu_privilege": menu_privilege,
                "menu_items": view_menus_list,
                "user_privilege_name": "",
            }
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = req.request("PUT", update_role_api_url, headers=headers, data=payload)

        if response.status_code == 200:

            messages.success(request, message=f"The menus updated successfully.")
            return redirect('user_privilege_screen', user_id)
        else:
            error_res = response.json()
            messages.error(request, message=f"{error_res['detail']}")

    # print(menu_res_json)
    # print(menu_pre_data)

    context = {
        "menu": "menu-userprivilege",
        "user_id": user_id,
        "menus_name_list": menus_name_list,
        "menu_privilege_list": menu_privilege_list,
        "menu_res_json": menu_res_json,
        "previous_menus_list": previous_menus_list,
        "menu_pre_data": menu_pre_data,
    }
    return render(request, 'users_manage/userprivilege/update_user_privilege.html', context)


def delete_user_privilege(request, user_id, psk_id):
    delete_user_api_url = f"{API_STUDIO_URL}deleteapi/delete/asa0505_01_01/{psk_id}"

    payload = {}
    headers = {}

    response = req.request("DELETE", delete_user_api_url, headers=headers, data=payload)

    if response.status_code == 200:
        messages.success(request, message=f"The privilege  was deleted successfully.")
        return redirect('user_privilege_screen', user_id)
    else:
        error_res = response.json()
        messages.error(request, message=f"{error_res['detail']}")

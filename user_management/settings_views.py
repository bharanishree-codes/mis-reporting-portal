from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
import requests as req
# import json, hashlib
# from .models import *
from .forms import *
import json

import configparser
import os


config = configparser.ConfigParser()
config.read(os.path.join(os.getcwd(), 'config.ini'))

# API_STUDIO_URL = "https://api.hcaschennai.edu.in/"
API_STUDIO_URL = config['DEFAULT']['STUDIO_URL']


# from user_management.views import fetch_user_photo


def dropdown_urls_get(request):
    if request.user.username == "admin":

        dropdown_menus = StudioMenus.objects.filter(menu_type='dropdown').all()

        # Filter dropdown menus with non-empty 'menu_href'
        res_data = [menu for menu in dropdown_menus if menu.menu_href]
        # print("res_data", res_data)
        return res_data

    else:
        user = request.user
        try:
            user_profile = UserProfile.objects.get(user=user)
            user_menus = user_profile.studio_menus.filter(menu_type='dropdown')
            res_data = [menu for menu in user_menus if menu.menu_href]
            return res_data

        except UserProfile.DoesNotExist:
            return []


def settings_data(request):
    api_url = f"{API_STUDIO_URL}getapi/asa0507_01_01/1"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code != 200:
        print("api not working")
    obj = response.json()
    return obj


def roles_tbl(request):
    if request.user.username == "admin":
        roles_tbl_url = f"{API_STUDIO_URL}getapi/asa0501_01_01/all"

        payload = {}
        headers = {}
        menu_privilege_response = req.request("GET", roles_tbl_url, headers=headers, data=payload)
        menu_privilege_list = menu_privilege_response.json()
        # print(menu_privilege_list)
        if menu_privilege_response.status_code != 200:
            messages.error(request, message="The API is not retrieving data.")
        return menu_privilege_list
    else:
        from .views import get_user_role_value

        user_data = get_user_role_value(request, request.user.last_name)
        # print("user_data", user_data)

        menu_privilege_list = []

        roles_tbl_url = f"{API_STUDIO_URL}getapi/asa0501_01_01/all"

        payload = {}
        headers = {}
        menu_privilege_response = req.request("GET", roles_tbl_url, headers=headers, data=payload)
        menu_privilege_list_datas = menu_privilege_response.json()

        for menu_item in menu_privilege_list_datas:
            if menu_item['psk_id'] in user_data:
                menu_privilege_list.append(menu_item)

        # print("menu_privilege_list", menu_privilege_list)

        return menu_privilege_list


def user_bundle_settings():
    # obj = SettingsModel.objects.get(id=1)

    api_url = f"{API_STUDIO_URL}getapi/asa0507_01_01/all"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code != 200:
        print("api not working")
    obj = response.json()[0]

    return obj['application_url']


API_STUDIO_URL = user_bundle_settings()


def get_settings(request):
    # print("function working")
    try:
        from .views import fetch_user_photo
        # Call your custom functions to get additional settings
        obj = settings_data(request)
        favicon_logo = favicorn_image_get(request)
        app_bar_logo = app_bar_logo_get(request)
        login_page_img = login_page_get(request)
        login_logo_img = login_logo_image_get(request)
        homepage_logo_img = home_page_logo_get(request)
        profile_img = fetch_user_photo(request)

        username = request.user.username

        # Define the API endpoint
        api_url = f"{API_STUDIO_URL}getapi/asa0507_01_01/all"

        # Make the GET request to the API
        response = req.get(api_url)

        # Check for a successful response
        if response.status_code != 200:
            print("API not working")
            return {
                'application_name': 'Default Application Name',  # Fallback value
                'favicon_caption': 'Default Caption',  # Fallback value
                'favicon_logo': favicon_logo,
            }

        # Parse the response JSON
        obj = response.json()[0]
        # print(obj)

        roles_tbl_data = roles_tbl(request)
        dropdown_urls = dropdown_urls_get(request)



        # Create a data dictionary to return
        data = {
            'application_name': obj.get('applicaton_name', 'Default Application Name'),  # Fallback for key errors
            'favicon_caption': obj.get('favicon_name', 'Default Caption'),  # Fallback for key errors
            'home_page_url': obj.get('home_page_url', ''),
            'home_page_name': obj.get('home_page_name', ''),
            'favicon_logo': favicon_logo,
            'app_bar_logo': app_bar_logo,
            'login_page_img': login_page_img,
            'login_logo_img': login_logo_img,
            'homepage_logo_img': homepage_logo_img,
            'photo_url': profile_img,
            'roles_tbl_data': roles_tbl_data,
            'dropdown_urls': dropdown_urls,
            'username': username

        }
        return data

    except Exception as e:
        # print(f"An error occurred: {e}")
        return {
            'application_name': obj.get('applicaton_name', 'Default Application Name'),  # Fallback for key errors
            'favicon_caption': obj.get('favicon_name', 'Default Caption'),  # Fallback for key errors
            'home_page_url': obj.get('home_page_url', ''),
            'home_page_name': obj.get('home_page_name', ''),
            'favicon_logo': favicon_logo,
            'app_bar_logo': app_bar_logo,
            'login_page_img': login_page_img,
            'login_logo_img': login_logo_img,
        }


def get_settings_ajax(request):
    obj = settings_data(request)
    favicon_logo = favicorn_image_get(request)

    api_url = f"{API_STUDIO_URL}getapi/asa0507_01_01/all"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code != 200:
        print("api not working")
    obj = response.json()[0]

    data = {
        'application_name': obj['applicaton_name'],
        'favicon_caption': obj['favicon_name'],
        'favicon_logo': favicon_logo,
    }
    return JsonResponse(data)


def settings_screen(request, user_id):
    api_url = f"{API_STUDIO_URL}getapi/asa0507_01_01/1"

    payload = {}
    headers = {}

    response = req.request("GET", api_url, headers=headers, data=payload)
    if response.status_code != 200:
        print("api not working")
    obj = response.json()
    context = {
        "menu": "menu-settings",
        "obj": obj,
        "user_id": user_id
    }
    return render(request, 'users_manage/settings_views/settings_screen.html', context)


def favicorn_image_get(request):
    photo_url = f"{API_STUDIO_URL}crudapp/view/media/asa0507_01_01_media/1"
    return photo_url


def login_logo_image_get(request):
    photo_url = f"{API_STUDIO_URL}crudapp/view/media/asa0507_01_01_media/2"
    return photo_url


def home_page_logo_get(request):
    photo_url = f"{API_STUDIO_URL}crudapp/view/media/asa0507_01_01_media/3"
    return photo_url


def app_bar_logo_get(request):
    photo_url = f"{API_STUDIO_URL}crudapp/view/media/asa0507_01_01_media/4"
    return photo_url


def login_page_get(request):
    photo_url = f"{API_STUDIO_URL}crudapp/view/media/asa0507_01_01_media/5"
    return photo_url


def update_image(file, psk_id, parent_psk_id, image_type='favicon'):
    """Helper function to update an image via the API."""

    # Determine the image URL based on the type of image being updated
    if image_type == 'favicon':
        image_url = f"{API_STUDIO_URL}crudapp/upload/media/asa0507_01_01_media/1"  # Favicon URL
    elif image_type == 'login_page_logo':
        image_url = f"{API_STUDIO_URL}crudapp/upload/media/asa0507_01_01_media/2"  # Login Page Logo URL
    elif image_type == 'home_page_logo':
        image_url = f"{API_STUDIO_URL}crudapp/upload/media/asa0507_01_01_media/3"
    elif image_type == 'app_bar_logo':
        image_url = f"{API_STUDIO_URL}crudapp/upload/media/asa0507_01_01_media/4"
    elif image_type == 'login_page':
        image_url = f"{API_STUDIO_URL}crudapp/upload/media/asa0507_01_01_media/5"
    else:
        raise ValueError("Invalid image type specified.")

    payload = {'parent_psk_id': parent_psk_id}
    # Use the file's name dynamically instead of hardcoding it
    files = [('media', (file.name, file, file.content_type))]

    headers = {
        'api_name': 'asa0507_01_01_media',
        'psk_id': str(psk_id)
    }

    response = req.put(image_url, headers=headers, data=payload, files=files)
    return response.status_code == 200


def settings_form(request, psk_id):
    apiurl = f"{API_STUDIO_URL}getapi/asa0507_01_01/{psk_id}"

    payload = {}
    headers = {}

    response = req.request("GET", apiurl, headers=headers, data=payload)

    if response.status_code != 200:
        messages.error(request, message="The API is not User Master Table retrieving data.")
        return redirect('settings_screen', request.user.id)  # Added redirect on error

    obj = response.json()

    favicon_image = favicorn_image_get(request)
    login_page_logo = login_logo_image_get(request)
    home_page_logo = home_page_logo_get(request)
    app_bar_logo = app_bar_logo_get(request)
    login_page = login_page_get(request)

    obj['favicon_logo'] = favicon_image
    obj['login_page_logo'] = login_page_logo
    obj['home_page_logo'] = home_page_logo
    obj['app_bar_logo'] = app_bar_logo
    obj['login_page'] = login_page

    if request.method == 'POST':
        app_name = request.POST['app_name']
        api_url = request.POST['api_url']
        favicon_caption = request.POST['favicon_caption']
        home_page_url = request.POST['home_page_url']
        home_page_name = request.POST['home_page_name']
        favicon_file = request.FILES.get('favicon_file')
        login_page_logo_file = request.FILES.get('login_page_logo')
        home_page_logo_file = request.FILES.get('home_page_logo')
        app_bar_logo_file = request.FILES.get('app_bar_logo')
        login_page_file = request.FILES.get('login_page')
        print(favicon_file)

        url = f"{API_STUDIO_URL}updateapi/update/asa0507_01_01/1"

        payload = json.dumps({
            "data": {
                "application_name": app_name,
                "application_url": api_url,
                "favicon_name": favicon_caption,
                "home_page_url": home_page_url,
                "home_page_name": home_page_name,

            }
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = req.request("PUT", url, headers=headers, data=payload)
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)

        if response.status_code != 200:
            messages.error(request, message="Api Not Working")

        # Update favicon image if uploaded
        if favicon_file:
            # Update favicon image
            success = update_image(favicon_file, psk_id=1, parent_psk_id=1, image_type='favicon')
            if not success:
                messages.error(request, message="Favicon API Not Working")

        if login_page_logo_file:
            # Update login page logo
            success = update_image(login_page_logo_file, psk_id=2, parent_psk_id=1, image_type='login_page_logo')
            if not success:
                messages.error(request, message="Login Page Logo API Not Working")

        if home_page_logo_file:
            # Update login page logo
            success = update_image(home_page_logo_file, psk_id=3, parent_psk_id=1, image_type='home_page_logo')
            if not success:
                messages.error(request, message="Login Page Logo API Not Working")

        if app_bar_logo_file:
            # Update login page logo
            success = update_image(app_bar_logo_file, psk_id=4, parent_psk_id=1, image_type='app_bar_logo')
            if not success:
                messages.error(request, message="Login Page Logo API Not Working")

        if login_page_file:
            # Update login page logo
            success = update_image(login_page_file, psk_id=5, parent_psk_id=1, image_type='login_page')
            if not success:
                messages.error(request, message="Login Page Logo API Not Working")

        messages.success(request, message="Updated successfully")
        return redirect('settings_screen', request.user.id)

    context = {
        "menu": "menu-settings",
        "user_id": request.user.id,
        "obj": obj
    }
    return render(request, 'users_manage/settings_views/settings_form.html', context)


# def settings_form(request, user_id, id):
#     obj = SettingsModel.objects.get(id=id)
#     # print(obj)
#
#     if request.method == 'POST':
#         app_name = request.POST['app_name']
#         api_url = request.POST['api_url']
#         favicon_caption = request.POST['favicon_caption']
#         favicon_file = request.FILES.get('favicon_file')
#
#         if favicon_file is None:
#             obj.application_name = app_name
#             obj.api_url = api_url
#             obj.favicon_caption = favicon_caption
#             obj.save()
#             messages.success(request, message="Uploaded successfully")
#             return redirect('settings_screen', user_id)
#
#         else:
#             obj.application_name = app_name
#             obj.api_url = api_url
#             obj.favicon_caption = favicon_caption
#             obj.favicon_logo = favicon_file
#             obj.save()
#             messages.success(request, message="Updated successfully")
#             return redirect('settings_screen', user_id)
#
#     context = {
#         "menu": "menu-settings",
#         "user_id": user_id,
#         "obj": obj
#     }
#     return render(request, 'users_manage/settings_views/settings_form.html', context)


def user_master_details(request, user_id):
    objs = MenusDetailsModel.objects.filter(starter_menu="user_master").all()
    for obj in objs:
        obj.api_methods_list = obj.api_method.split(',')
    context = {
        "menu": "menu-usermaster-details",
        "objs": objs,
        "user_id": user_id
    }
    return render(request, 'users_manage/settings_views/user_master_details.html', context)


def um_details_form(request, user_id):
    form = UserMasterDetailsForm()

    if request.method == 'POST':
        form = UserMasterDetailsForm(request.POST)
        api_methods_list = request.POST.getlist('api_list')
        api_methods_uses = ','.join(map(str, api_methods_list))

        if form.is_valid():
            obj = form.save(commit=False)
            obj.starter_menu = "user_master"
            obj.api_method = api_methods_uses
            obj.save()
            return redirect('user_master_details', user_id)
        else:
            messages.error(request, 'form is invalid.')

    context = {
        "menu": "menu-usermaster-details",
        "user_id": user_id,
        "form": form,
        "form_name": "User Master / Details Form"
    }
    return render(request, 'users_manage/settings_views/form.html', context)


def edit_um_details_form(request, user_id, id):
    prev_obj = MenusDetailsModel.objects.get(id=id)
    prev_api_methods_list = prev_obj.api_method.split(',')
    # print(prev_obj.api_method)
    form = UserMasterDetailsForm(instance=prev_obj)

    if request.method == 'POST':
        form = UserMasterDetailsForm(request.POST, instance=prev_obj)
        api_methods_list = request.POST.getlist('api_list')
        # print(api_methods_list)
        # Convert the list of integers to a comma-separated string
        api_methods_uses = ','.join(map(str, api_methods_list))
        if form.is_valid():
            obj = form.save(commit=False)
            obj.starter_menu = "user_master"
            obj.api_method = api_methods_uses
            obj.save()
            return redirect('user_master_details', user_id)
        else:
            messages.error(request, 'form is invalid.')

    context = {
        "menu": "menu-usermaster-details",
        "form": form,
        "prev_api_methods": prev_api_methods_list,
        "form_name": "User Master / Details Form",
        "user_id": user_id,
    }
    return render(request, 'users_manage/settings_views/form.html', context)


def roles_master_details(request, user_id):
    objs = MenusDetailsModel.objects.filter(starter_menu="roles_master").all()
    for obj in objs:
        obj.api_methods_list = obj.api_method.split(',')
    context = {
        "menu": "menu-rolesmaster-details",
        "user_id": user_id,
        "objs": objs
    }
    return render(request, 'users_manage/settings_views/roles_master_details.html', context)


def roles_details_form(request, user_id):
    form = UserMasterDetailsForm()

    if request.method == 'POST':
        form = UserMasterDetailsForm(request.POST)
        api_methods_list = request.POST.getlist('api_list')
        api_methods_uses = ','.join(map(str, api_methods_list))
        if form.is_valid():
            obj = form.save(commit=False)
            obj.starter_menu = "roles_master"
            obj.api_method = api_methods_uses
            obj.save()
            return redirect('roles_master_details', user_id)
        else:
            messages.error(request, 'form is invalid.')

    context = {
        "menu": "menu-rolesmaster-details",
        "user_id": user_id,
        "form": form,
        "form_name": "Roles Master / Details Form"
    }
    return render(request, 'users_manage/settings_views/form.html', context)


def edit_roles_details_form(request, user_id, id):
    prev_obj = MenusDetailsModel.objects.get(id=id)
    prev_api_methods_list = prev_obj.api_method.split(',')
    form = UserMasterDetailsForm(instance=prev_obj)

    if request.method == 'POST':
        form = UserMasterDetailsForm(request.POST, instance=prev_obj)
        api_methods_list = request.POST.getlist('api_list')
        api_methods_uses = ','.join(map(str, api_methods_list))
        if form.is_valid():
            obj = form.save(commit=False)
            obj.starter_menu = "roles_master"
            obj.api_method = api_methods_uses
            obj.save()
            return redirect('roles_master_details', user_id)
        else:
            messages.error(request, 'form is invalid.')

    context = {
        "menu": "menu-rolesmaster-details",
        "user_id": user_id,
        "form": form,
        "prev_api_methods": prev_api_methods_list,
        "form_name": "Roles Master / Details Form"
    }
    return render(request, 'users_manage/settings_views/form.html', context)


def user_privi_details(request, user_id):
    objs = MenusDetailsModel.objects.filter(starter_menu="user_privilege").all()
    for obj in objs:
        obj.api_methods_list = obj.api_method.split(',')
    context = {
        "menu": "menu-userprivilege-details",
        "user_id": user_id,
        "objs": objs
    }
    return render(request, 'users_manage/settings_views/user_privi_details.html', context)


def user_privi_form(request, user_id):
    form = UserMasterDetailsForm()

    if request.method == 'POST':
        form = UserMasterDetailsForm(request.POST)
        api_methods_list = request.POST.getlist('api_list')
        api_methods_uses = ','.join(map(str, api_methods_list))
        if form.is_valid():
            obj = form.save(commit=False)
            obj.starter_menu = "user_privilege"
            obj.api_method = api_methods_uses
            obj.save()
            return redirect('user_privi_details', user_id)
        else:
            messages.error(request, 'form is invalid.')

    context = {
        "menu": "menu-userprivilege-details",
        "user_id": user_id,
        "form": form,
        "form_name": "User Privilege  / Details Form"
    }
    return render(request, 'users_manage/settings_views/form.html', context)


def edit_user_privi_form(request, user_id, id):
    prev_obj = MenusDetailsModel.objects.get(id=id)
    prev_api_methods_list = prev_obj.api_method.split(',')
    form = UserMasterDetailsForm(instance=prev_obj)

    if request.method == 'POST':
        form = UserMasterDetailsForm(request.POST, instance=prev_obj)
        api_methods_list = request.POST.getlist('api_list')
        api_methods_uses = ','.join(map(str, api_methods_list))
        if form.is_valid():
            obj = form.save(commit=False)
            obj.starter_menu = "user_privilege"
            obj.api_method = api_methods_uses
            obj.save()
            return redirect('user_privi_details', user_id)
        else:
            messages.error(request, 'form is invalid.')

    context = {
        "menu": "menu-userprivilege-details",
        "user_id": user_id,
        "form": form,
        "prev_api_methods": prev_api_methods_list,
        "form_name": "User Privilege  / Details Form"
    }
    return render(request, 'users_manage/settings_views/form.html', context)


def menu_element_details(request, user_id):
    objs = MenusDetailsModel.objects.filter(starter_menu="menu_elements").all()
    for obj in objs:
        obj.api_methods_list = obj.api_method.split(',')
    context = {
        "menu": "menu-menuelements-details",
        "user_id": user_id,
        "objs": objs
    }
    return render(request, 'users_manage/settings_views/menu_elements_details.html', context)


def menu_element_detail_form(request, user_id):
    form = UserMasterDetailsForm()

    if request.method == 'POST':
        form = UserMasterDetailsForm(request.POST)
        api_methods_list = request.POST.getlist('api_list')
        api_methods_uses = ','.join(map(str, api_methods_list))
        if form.is_valid():
            obj = form.save(commit=False)
            obj.starter_menu = "menu_elements"
            obj.api_method = api_methods_uses
            obj.save()
            return redirect('menu_element_details', user_id)
        else:
            messages.error(request, 'form is invalid.')

    context = {
        "menu": "menu-menuelements-details",
        "user_id": user_id,
        "form": form,
        "form_name": "Menu Elements / Details Form"
    }
    return render(request, 'users_manage/settings_views/form.html', context)


def edit_menu_element_detail_form(request, user_id, id):
    prev_obj = MenusDetailsModel.objects.get(id=id)
    prev_api_methods_list = prev_obj.api_method.split(',')
    form = UserMasterDetailsForm(instance=prev_obj)

    if request.method == 'POST':
        form = UserMasterDetailsForm(request.POST, instance=prev_obj)
        api_methods_list = request.POST.getlist('api_list')
        api_methods_uses = ','.join(map(str, api_methods_list))
        if form.is_valid():
            obj = form.save(commit=False)
            obj.starter_menu = "menu_elements"
            obj.api_method = api_methods_uses
            obj.save()
            return redirect('menu_element_details', user_id)
        else:
            messages.error(request, 'form is invalid.')

    context = {
        "menu": "menu-menuelements-details",
        "user_id": user_id,
        "form": form,
        "prev_api_methods": prev_api_methods_list,
        "form_name": "Menu Elements / Details Form"
    }
    return render(request, 'users_manage/settings_views/form.html', context)


def menu_privilege_details(request, user_id):
    objs = MenusDetailsModel.objects.filter(starter_menu="menu_privilege").all()
    for obj in objs:
        obj.api_methods_list = obj.api_method.split(',')
    context = {
        "menu": "menu-menuprivilege-details",
        "user_id": user_id,
        "objs": objs
    }
    return render(request, 'users_manage/settings_views/menu_privilege_details.html', context)


def menu_privilege_detail_form(request, user_id):
    form = UserMasterDetailsForm()

    if request.method == 'POST':
        form = UserMasterDetailsForm(request.POST)
        api_methods_list = request.POST.getlist('api_list')
        api_methods_uses = ','.join(map(str, api_methods_list))
        if form.is_valid():
            obj = form.save(commit=False)
            obj.starter_menu = "menu_privilege"
            obj.api_method = api_methods_uses
            obj.save()
            return redirect('menu_privilege_details', user_id)
        else:
            messages.error(request, 'form is invalid.')

    context = {
        "menu": "menu-menuprivilege-details",
        "user_id": user_id,
        "form": form,
        "form_name": "Menu Privilege / Details Form"
    }
    return render(request, 'users_manage/settings_views/form.html', context)


def edit_menu_privilege_detail_form(request, user_id, id):
    prev_obj = MenusDetailsModel.objects.get(id=id)
    prev_api_methods_list = prev_obj.api_method.split(',')
    form = UserMasterDetailsForm(instance=prev_obj)

    if request.method == 'POST':
        form = UserMasterDetailsForm(request.POST, instance=prev_obj)
        api_methods_list = request.POST.getlist('api_list')
        api_methods_uses = ','.join(map(str, api_methods_list))
        if form.is_valid():
            obj = form.save(commit=False)
            obj.starter_menu = "menu_privilege"
            obj.api_method = api_methods_uses
            obj.save()
            return redirect('menu_privilege_details', user_id)
        else:
            messages.error(request, 'form is invalid.')

    context = {
        "menu": "menu-menuprivilege-details",
        "user_id": user_id,
        "form": form,
        "prev_api_methods": prev_api_methods_list,
        "form_name": "Menu Privilege / Details Form"
    }
    return render(request, 'users_manage/settings_views/form.html', context)

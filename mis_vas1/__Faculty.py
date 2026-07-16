from openpyxl.styles import Font
from turtle import pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
import requests
import json
from datetime import datetime
from collections import Counter
from user_management.settings_views import get_settings
from MIS.functions import validate_file_format_faculty, validate_file_size
from user_management.settings_views import *

API_STUDIO_URL = user_bundle_settings()

PARTICIPATION_OPTIONS = [
    'Board of Studies', 'Question Paper Setting', 'Evaluation', 
    'Add-On (Other University & College)', 'Certificate Courses',
    'External Examiner', 'Conference', 'Seminar', 'Workshop', 'Faculty Development Program'
]

def faculty_auth():
    url = f"{API_STUDIO_URL}auth/token"
    payload = json.dumps({"secret_key": "C4ZoXbsAnHLjk1Xyz4QPT2eoiNx6K6fo"})
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        response_data = response.json()
        return response_data.get('access_token'), response_data.get('token_type')
    return None, None

def faculty_token(access_token, token_type):
    url = f"{API_STUDIO_URL}sqlviews/api/v1/auth/get_response_data"
    payload = json.dumps({
        "psk_uid": "51a531b4-bd55-491c-861d-a8d7227b325b",
        "project": "hcas",
        "data": {}
    })
    headers = {
        'Content-Type': 'application/json', 
        'Authorization': f'{token_type} {access_token}'
    }
    response = requests.post(url, headers=headers, data=payload)
    return response.json() if response.status_code == 200 else None

def create_participation(request):
    access_token, token_type = faculty_auth()
    if not access_token or not token_type:
        return render(request, 'ParticipationFaculty_templates/create_participation.html', 
                     {'error': 'Failed to get access token from API.'})

    faculty_data = faculty_token(access_token, token_type)
    if not faculty_data:
        return render(request, 'ParticipationFaculty_templates/create_participation.html', 
                     {'error': 'Failed to fetch staff data.'})

    current_year = datetime.now().year
    years = [f"{y}-{y+1}" for y in range(current_year, 2010, -1)]
    
    user = get_settings(request)
    # username = user.get('username', '')
    username = 'CS-T151'
    
    selected_faculty = None
    for faculty in faculty_data:
        if faculty.get('stf_id') == username:
            selected_faculty = faculty
            break
    
    stf_name = selected_faculty.get('stf_name', '') if selected_faculty else ''
    department = selected_faculty.get('department', '') if selected_faculty else ''

    if request.method == 'POST':
        selected_options = request.POST.getlist('items')
        year = request.POST.get('year')
        name = request.POST.get('name')
        stf_id = username

        selected_faculty = None
        for faculty in faculty_data:
            if faculty.get('stf_id') == stf_id:
                selected_faculty = faculty
                break

        if selected_faculty:
            depcode = selected_faculty.get('depcode', '')
            department = selected_faculty.get('department', '')
            stf_name = selected_faculty.get('stf_name', '')
            
            url = f"{API_STUDIO_URL}postapi/create/naac01_faculty_participation_dc1"
            create_data = {
                "data": {
                    "name": name, 
                    "year": year, 
                    "participation": ', '.join(selected_options), 
                    "stf_id": stf_id, 
                    "depcode": depcode, 
                    "department": department, 
                    "stf_name": stf_name
                }
            }
            
            headers = {'Content-Type': 'application/json', 'Authorization': f'{token_type} {access_token}'}
            response = requests.post(url, headers=headers, data=json.dumps(create_data))
            
            if response.status_code == 200:
                psk_id = response.json().get('psk_id')
                return redirect('detail_view', id=psk_id)
            else:
                return HttpResponse("Failure: " + response.text)
        else:
            return render(request, 'ParticipationFaculty_templates/create_participation.html', 
                         {'error': "Selected faculty not found.", 'options': PARTICIPATION_OPTIONS, 
                          'faculty_data': faculty_data, 'years': years, 'staff_id': username, 
                          'stf_name': stf_name, 'department': department})
    
    return render(request, 'ParticipationFaculty_templates/create_participation.html', 
                 {'options': PARTICIPATION_OPTIONS, 'faculty_data': faculty_data, 'years': years, 
                  'staff_id': username, 'stf_name': stf_name, 'department': department})

def detail_view(request, id):
    current_year = datetime.now().year
    years = [f"{y}-{y+1}" for y in range(current_year, 2010, -1)]
    
    parent_url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc1/{id}"
    parent_res = requests.get(parent_url)

    if parent_res.status_code != 200:
        return HttpResponse(f"Error fetching participation details: {parent_res.text}")

    participation = parent_res.json()
    parent_id = participation.get('psk_id')
    selected_options = participation.get('participation', '').split(', ')
    year = request.POST.get('year', participation.get('year', ''))

    payload = json.dumps({
        "queries": [{"field": "transaction_id", "value": parent_id, "operation": "equal"}],
        "search_type": "all"
    })
    
    child_res = requests.get(
        url=f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc2", 
        headers={'Content-Type': 'application/json'}, 
        data=payload
    )

    children = child_res.json() if child_res.status_code == 200 else []

    for child in children:
        child_id = child.get('psk_id')
        media_url = f"{API_STUDIO_URL}crudapp/get/media/naac01_faculty_participation_dc2_media/parent/{child_id}"
        media_res = requests.get(media_url)
        child['media'] = [item.get('file_name') for item in media_res.json()] if media_res.status_code == 200 else []

        # Convert date_from and date_to to DD-MM-YYYY format
        for date_field in ['date_from', 'date_to']:
            date_val = child.get(date_field)
            if date_val:
                parts = date_val.split('-')
                # handle YYYY-MM-DD → DD-MM-YYYY
                if len(parts[0]) == 4:
                    child[date_field] = f"{parts[2]}-{parts[1]}-{parts[0]}"
                # already DD-MM-YYYY
                else:
                    child[date_field] = date_val
            else:
                child[date_field] = ""


    field_map = {
        'board of studies': ['board_university_college_name', 'board_designation'],
        'question paper setting': ['qp_university_college_name', 'qp_subject'],
        'evaluation': ['eval_university_college_name', 'eval_subject'],
        'Add-On (Other University & College)': ['design_development_university_college_name', 'design_development_addon'],
        'certificate courses': ['certificate_university_college_name', 'certificate_course'],
        'external examiner': ['external_examiner_university_college_name'],
        'conference': ['conference_university_college_name', 'conference_name'],
        'seminar': ['seminar_university_college_name', 'seminar_name'],
        'workshop': ['workshop_university_college_name', 'workshop_name'],
        'faculty development program': ['name_of_the_resource_person', 'name_of_the_program', 'date_from', 'date_to']
    }

    missing_children = []
    if request.method == 'POST':
        for option in selected_options:
            key = option.lower()
            fields = field_map.get(key, [])
            has_valid_child = any(all(child.get(f) for f in fields) for child in children)
            if not has_valid_child:
                missing_children.append(option)

        if missing_children:
            messages.error(request, f"The following selections are missing required data: {', '.join(missing_children)}")
            return render(request, "ParticipationFaculty_templates/detail_view.html", 
                         {'participation': participation, 'selected_options': selected_options, 
                          'children': children, 'year': year, 'missing_children': missing_children})

        messages.success(request, "Participation data processed successfully!")
        return redirect('list_participations')

    return render(request, "ParticipationFaculty_templates/detail_view.html", 
                 {'participation': participation, 'selected_options': selected_options, 
                  'children': children, 'year': year, 'missing_children': [], 'years': years})

def list_participations(request):
    cleanup_orphan_participations()
    
    url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc1/all"
    response = requests.get(url)
    
    if response.status_code != 200:
        return HttpResponse("API Call Is Not Working")

    participations = response.json()
    user = get_settings(request)
    # username = user.get('username', '')
    username = 'CS-T151'
    
    filtered_participations = [
        participation for participation in participations 
        if participation.get('stf_id') == username
    ]
    
    selected_staff_id = request.GET.get('staff_id')
    if selected_staff_id:
        filtered_participations = [
            participation for participation in participations 
            if participation.get('stf_id') == selected_staff_id
        ]
    
    if not filtered_participations:
        return render(request, 'ParticipationFaculty_templates/list_participations.html', 
                     {"participations": []})
    
    return render(request, 'ParticipationFaculty_templates/list_participations.html', 
                 {"participations": filtered_participations})

def cleanup_orphan_participations():
    parent_url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc1/all"
    parent_res = requests.get(parent_url)
    
    if parent_res.status_code != 200:
        return
    
    all_parents = parent_res.json()
    
    for parent in all_parents:
        parent_id = parent.get("psk_id")
        if not parent_id:
            continue
        
        child_url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc2"
        payload = json.dumps({
            "queries": [{"field": "transaction_id", "value": parent_id, "operation": "equal"}],
            "search_type": "all"
        })
        headers = {'Content-Type': 'application/json'}
        children_response = requests.get(child_url, headers=headers, data=payload)
        
        children = children_response.json() if children_response.status_code == 200 else []
        
        if not children:
            delete_url = f"{API_STUDIO_URL}deleteapi/delete/naac01_faculty_participation_dc1/{parent_id}"
            requests.delete(delete_url)

def update_participation(request, id):
    try:
        url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc1/{id}"
        response = requests.get(url)
        
        if response.status_code != 200:
            return HttpResponse(f"Error fetching participation data: {response.text}", status=500)
            
        participation = response.json()
        
        current_year = datetime.now().year
        years = [f"{y}-{y+1}" for y in range(current_year, 2010, -1)]
        selected_options = participation.get('participation', '').split(', ') if 'participation' in participation else []
        
        my_child = []
        try:
            children_url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc2"
            payload = json.dumps({
                "queries": [{"field": "transaction_id", "value": id, "operation": "equal"}], 
                "search_type": "all"
            })
            headers = {'Content-Type': 'application/json'}
            
            children_response = requests.post(children_url, headers=headers, data=payload)
            
            if children_response.status_code == 200:
                my_child = children_response.json()
        except Exception:
            pass
        
        if request.method == "POST":
            selected_options_from_form = request.POST.getlist('items')
            
            options_with_children = []
            
            if my_child:
                field_map = {
                    'board of studies': ['board_university_college_name', 'board_designation'],
                    'question paper setting': ['qp_university_college_name', 'qp_subject'],
                    'evaluation': ['eval_university_college_name', 'eval_subject'],
                    'Add-On (Other University & College)': ['design_development_university_college_name', 'design_development_addon'],
                    'certificate courses': ['certificate_university_college_name', 'certificate_course'],
                    'external examiner': ['external_examiner_university_college_name'],
                    'conference': ['conference_university_college_name', 'conference_name'],
                    'seminar': ['seminar_university_college_name', 'seminar_name'],
                    'workshop': ['workshop_university_college_name', 'workshop_name'],
                    'faculty development program': ['name_of_the_resource_person', 'name_of_the_program', 'date_from', 'date_to']
                }
                
                for option in selected_options:
                    option_key = option.lower()
                    has_children = False
                    
                    required_fields = field_map.get(option_key, [])
                    if required_fields:
                        for child in my_child:
                            if all(child.get(field) for field in required_fields):
                                has_children = True
                                break
                                
                        if has_children and option not in selected_options_from_form:
                            options_with_children.append(option)
            
            if options_with_children:
                error_message = f"Cannot deselect the following options because they have associated children: {', '.join(options_with_children)}"
                messages.error(request, error_message)
                
                return render(request, 'ParticipationFaculty_templates/update_participation.html', {
                    'participation': participation,
                    'selected_options': selected_options,
                    'years': years,
                    'options': PARTICIPATION_OPTIONS
                })
            
            name = request.POST.get('name', participation.get('name', ''))
            year = request.POST.get('year', participation.get('year', ''))
            participation_type = ', '.join(request.POST.getlist('items'))
            
            update_url = f"{API_STUDIO_URL}updateapi/update/naac01_faculty_participation_dc1/{id}"
            payload = json.dumps({
                "data": {
                    "name": name, 
                    "year": year, 
                    "participation": participation_type
                }
            })
            headers = {'Content-Type': 'application/json'}
            update_response = requests.put(update_url, headers=headers, data=payload)
            
            if update_response.status_code == 200:
                return redirect('detail_view', id=participation.get('psk_id'))
            else:
                return HttpResponse("Failed to update participation: " + update_response.text)
        
        return render(request, 'ParticipationFaculty_templates/update_participation.html', {
            'participation': participation,
            'selected_options': selected_options,
            'years': years,
            'options': PARTICIPATION_OPTIONS
        })
        
    except Exception as e:
        return HttpResponse(f"Unexpected error: {str(e)}", status=500)

def delete_participation(request, id):
    delete_url = f"{API_STUDIO_URL}deleteapi/delete/naac01_faculty_participation_dc1/{id}"
    
    delete_response = requests.delete(delete_url)

    if delete_response.status_code == 200:
        messages.success(request, "The Article was deleted successfully.")
        return redirect('list_participations')
    else:
        error_msg = delete_response.json()
        messages.error(request, f"{error_msg.get('detail', 'Failed to delete participation')}")

def list_all_participation_children(request):
    participation_api = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc1/all"
    response = requests.get(participation_api)
    if response.status_code != 200:
        return HttpResponse("Could not load participation data")
    participation_data = response.json()

    user = get_settings(request)
    # username = user.get('username', '')
    username = 'CS-T151'
    final_staff_id = request.GET.get("staff_id") or username

    selected_category = request.GET.get("category")
    categories = [
        "Board of Studies", "Question Paper Setting", "Evaluation", "Design and Development", 
        "Certificate Courses", "External Examiner", "Conference", "Seminar", "Workshop", 
        'Faculty Development Program'
    ]

    filtered_data = [
        participation for participation in participation_data 
        if participation.get("stf_id") == final_staff_id and 
        (not selected_category or selected_category in [
            category.strip() for category in participation.get("participation", "").split(",")
        ])
    ]

    selected_types = {selected_category} if selected_category in categories else {
        child.strip() for parent in filtered_data for child in parent.get("participation", "").split(",") if child.strip() in categories}

    counts = Counter(
        t.strip().replace(" ", "_") for parent in filtered_data 
        for t in parent.get("participation", "").split(",") if t.strip()
    )

    child_api = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc2/all"
    child_response = requests.get(child_api)
    if child_response.status_code != 200:
        return HttpResponse("Could not load child records")
    child_data = child_response.json()

    staff_psk_ids = {parent.get("psk_id") for parent in filtered_data}
    final_children = []

    for cat in selected_types:
        key_map = {
            "Board of Studies": "board_university_college_name",
            "Question Paper Setting": "qp_university_college_name",
            "Evaluation": "eval_university_college_name",
            "Design and Development": "design_development_university_college_name",
            "Certificate Courses": "certificate_university_college_name",
            "External Examiner": "external_examiner_university_college_name",
            "Conference": "conference_university_college_name",
            "Seminar": "seminar_university_college_name",
            "Workshop": "workshop_university_college_name",
            "Faculty Development Program": 'name_of_the_resource_person',
        }
        field = key_map.get(cat)
        matching_children = [
            child for child in child_data 
            if child.get("transaction_id") in staff_psk_ids and child.get(field)
        ]

        for child in matching_children:
            child["media"] = []
            psk_id = child.get("psk_id")
            if psk_id:
                media_url = f"{API_STUDIO_URL}crudapp/get/media/naac01_faculty_participation_dc2_media/parent/{psk_id}"
                media_response = requests.get(media_url)
                if media_response.status_code == 200:
                    child["media"] = [m.get("file_name") for m in media_response.json()]

        final_children.append((cat, matching_children))

    return render(request, "ParticipationFaculty_templates/list_participation_children.html", {
        "participation": filtered_data,
        "selected_options": selected_types,
        "children_by_option": final_children,
        "participation_counts": counts,
        "username": final_staff_id
    })

def create_participation_child(request, participation_id, val):
    url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc1/{participation_id}"
    participation_parent_response = requests.get(url)
    if participation_parent_response.status_code != 200:
        return HttpResponse("Error fetching participation details: " + participation_parent_response.text)
    
    participation_parent = participation_parent_response.json()
    transaction_id = participation_parent.get('psk_id')
    selected_options = participation_parent.get('participation', '').split(', ') if participation_parent.get('participation') else []

    if request.method == 'POST':
        child_url = f"{API_STUDIO_URL}postapi/create/naac01_faculty_participation_dc2"

        def format_date(date_val):
            """Ensure date is always returned as string in DD-MM-YYYY format"""
            if not date_val:
                return ""
            if isinstance(date_val, datetime):
                return date_val.strftime("%d-%m-%Y")
            
            date_str = str(date_val)  # ✅ force into string
            try:
                # if input is YYYY-MM-DD
                if len(date_str.split('-')[0]) == 4:
                    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")
                # if input is already DD-MM-YYYY
                if len(date_str.split('-')[2]) == 4:
                    return date_str
            except Exception:
                return ""
            return ""

        # ✅ always stringify request.POST values before formatting
        date_from = format_date(request.POST.get('date_from', ""))
        date_to = format_date(request.POST.get('date_to', ""))

        payload = {
            'board_university_college_name': request.POST.get('board_university'),
            'board_designation': request.POST.get('board_designation'),
            'qp_university_college_name': request.POST.get('qp_university'),
            'qp_subject': request.POST.get('qp_subject'),
            'eval_university_college_name': request.POST.get('eval_institute'),
            'eval_subject': request.POST.get('eval_role'),
            'certificate_university_college_name': request.POST.get('cert_institute'),
            'certificate_course': request.POST.get('cert_course_name'),
            'external_examiner_university_college_name': request.POST.get('external_institute'),
            'conference_university_college_name': request.POST.get('conf_name'),
            'conference_name': request.POST.get('conf_role'),
            'seminar_university_college_name': request.POST.get('seminar_title'),
            'seminar_name': request.POST.get('seminar_role'),
            'workshop_university_college_name': request.POST.get('workshop_title'),
            'workshop_name': request.POST.get('workshop_role'),
            'design_development_university_college_name': request.POST.get('curriculum_institute'),
            'design_development_addon': request.POST.get('curriculum_role'),
            'name_of_the_resource_person': request.POST.get('name_of_the_resource_person'),
            'name_of_the_program': request.POST.get('name_of_the_program'),
            'date_from': date_from,
            'date_to': date_to,
            'transaction_id': transaction_id
        }

        headers = {'Content-Type': 'application/json'}
        response = requests.post(child_url, headers=headers, data=json.dumps({"data": payload}))

        if response.status_code != 200:
            return HttpResponse("Failed to create participation child: " + response.text)

        child_data = response.json()
        child_id = child_data.get('psk_id')

        media_url = f"{API_STUDIO_URL}crudapp/upload/media/naac01_faculty_participation_dc2_media/"
        uploaded_file = request.FILES.get('file')
        
        if uploaded_file:
            validate_file_size(uploaded_file)
            validate_file_format_faculty(uploaded_file)

            file_type = uploaded_file.content_type
            payload = {'parent_psk_id': child_id}
            files = {'media': (uploaded_file.name, uploaded_file, file_type)}
            headers = {'api_name': 'naac01_faculty_participation_dc2_media'}

            media_response = requests.post(media_url, headers=headers, data=payload, files=files)

            if media_response.status_code != 200:
                return HttpResponse("Failed to upload media files: " + media_response.text)

        return redirect('detail_view', id=participation_id)
    
    return render(
        request,
        'ParticipationFaculty_templates/create_participation_child.html',
        {'val': val, 'participation': participation_parent, 'selected_options': selected_options}
    )

def update_participation_child(request, participation_id, child_id, val):
    url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc1/{participation_id}"
    participation_parent_response = requests.get(url)
    
    if participation_parent_response.status_code != 200:
        return HttpResponse(f"Error fetching participation details: {participation_parent_response.text}")

    participation_parent = participation_parent_response.json()
    name = participation_parent.get('name')
    year = participation_parent.get('year')
    selected_options = participation_parent.get('participation', '').split(', ') if participation_parent.get('participation') else []

    child_url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc2/{child_id}"
    headers = {'Content-Type': 'application/json'}
    response = requests.get(child_url, headers=headers)

    if response.status_code != 200:
        return HttpResponse(f"Failed to fetch child data: {response.text}")

    child_data = response.json()

    media_url = f"{API_STUDIO_URL}crudapp/get/media/naac01_faculty_participation_dc2_media/parent/{child_id}"
    media_response = requests.get(media_url, headers=headers)

    value_id = None
    file_name = None
    if media_response.status_code == 200:
        media_data = media_response.json()
        if media_data:
            value_id = media_data[0]['psk_id']
            file_name = media_data[0]['file_name']

    if request.method == 'POST':
        update_url = f"{API_STUDIO_URL}updateapi/update/naac01_faculty_participation_dc2/{child_id}"

        payload = json.dumps({"data": {
            "board_university_college_name": request.POST.get('board_university', ''),
            "board_designation": request.POST.get('board_designation', ''),
            "qp_university_college_name": request.POST.get('qp_university', ''),
            "qp_subject": request.POST.get('qp_subject', ''),
            "eval_university_college_name": request.POST.get('eval_institute', ''),
            "eval_subject": request.POST.get('eval_role', ''),
            "certificate_university_college_name": request.POST.get('cert_institute', ''),
            "certificate_course": request.POST.get('cert_course_name', ''),
            "external_examiner_university_college_name": request.POST.get('external_institute', ''),
            "conference_university_college_name": request.POST.get('conf_name', ''),
            "conference_name": request.POST.get('conf_role', ''),
            "seminar_university_college_name": request.POST.get('seminar_title', ''),
            "seminar_name": request.POST.get('seminar_role', ''),
            "workshop_university_college_name": request.POST.get('workshop_title', ''),
            "workshop_name": request.POST.get('workshop_role', ''),
            "design_development_university_college_name": request.POST.get('curriculum_institute', ''),
            "design_development_addon": request.POST.get('curriculum_role', ''),
            "name_of_the_resource_person": request.POST.get('name_of_the_resource_person', ''),
            "name_of_the_program": request.POST.get('name_of_the_program', ''),
            "date_from": request.POST.get('date_from', ''),
            "date_to": request.POST.get('date_to', ''),
        }})
        
        headers = {'Content-Type': 'application/json'}
        update_response = requests.put(update_url, headers=headers, data=payload)

        if update_response.status_code != 200:
            return HttpResponse(f"Failed to update participation child: {update_response.text}")

        uploaded_file = request.FILES.get('file')
        if uploaded_file and value_id:
            validate_file_size(uploaded_file)
            validate_file_format_faculty(uploaded_file)
            
            url = f"{API_STUDIO_URL}crudapp/upload/media/naac01_faculty_participation_dc2_media/{value_id}"
            file_type = uploaded_file.content_type
            payload = {'parent_psk_id': child_id}
            files = {'media': (uploaded_file.name, uploaded_file, file_type)}
            headers = {'api_name': 'naac01_faculty_participation_dc2_media', 'psk_id': str(value_id)}

            upload_response = requests.put(url, headers=headers, data=payload, files=files)

            if upload_response.status_code != 200:
                return HttpResponse(f"Failed to upload media files: {upload_response.text}")

        return redirect('detail_view', id=participation_id)

    return render(request, 'ParticipationFaculty_templates/update_participation_child.html', {
        'val': val, 'participation': participation_id, 'child': child_data, 'name': name, 
        'year': year, 'selected_options': selected_options, 'value_id': value_id, 
        'id': participation_id, 'file_name': file_name
    })

def delete_participation_child(request, child_id, participation_id):
    delete_url = f"{API_STUDIO_URL}deleteapi/delete/naac01_faculty_participation_dc2/{child_id}"

    delete_response = requests.delete(delete_url)

    if delete_response.status_code == 200:
        messages.success(request, "The child participation was deleted successfully.")
    else:
        error_msg = delete_response.json() if delete_response.status_code == 400 else {}
        messages.error(request, f"Failed to delete child participation: {error_msg.get('detail', 'Unknown error')}")
    
    return redirect('detail_view', id=participation_id)

def list_options_participations(request):
    url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc1/all"
    response = requests.get(url)
    
    if response.status_code != 200:
        return HttpResponse("API Call Is Not Working")

    participations = response.json()

    option_counter = Counter()
    for participation in participations:
        options = participation.get('participation', '')
        if options:
            option_list = [opt.strip() for opt in options.split(',')]
            option_counter.update(option_list)

    participation_option_counts = {option: option_counter.get(option, 0) for option in PARTICIPATION_OPTIONS}

    return render(request, 'ParticipationFaculty_templates/list_options_participations.html', {
        'participations': participations,
        'participation_option_counts': participation_option_counts
    })
    
    
    
    
# def filter_participations(request):
#     """
#     Main filtering function for participations with Excel and PDF export
#     """
#     # Get all parent participations
#     parent_url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc1/all"
#     parent_response = requests.get(parent_url)
    
#     if parent_response.status_code != 200:
#         return HttpResponse("Error fetching participation data")
    
#     all_parents = parent_response.json()
    
#     # Get all child participations
#     child_url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc2/all"
#     child_response = requests.get(child_url)
    
#     all_children = child_response.json() if child_response.status_code == 200 else []
    
#     media_url = f"{API_STUDIO_URL}crudapp/get/media/naac01_faculty_participation_dc2_media/parent/{child_id}"
    
#     # Get filter parameters from request
#     stf_id = request.GET.get('stf_id', '').strip()
#     from_year = request.GET.get('from_year', '').strip()
#     to_year = request.GET.get('to_year', '').strip()
#     selected_options = request.GET.getlist('options')
#     export_format = request.GET.get('export', '')
    
#     # Filter parents
#     filtered_parents = all_parents
    
#     if stf_id:
#         filtered_parents = [parent for parent in filtered_parents if parent.get('stf_id') == stf_id]
    
#     # Convert year values to integers for comparison
#     if from_year:
#         try:
#             from_year_int = int(from_year.split('-')[0])  # Extract first year from "YYYY-YYYY" format
#             filtered_parents = [parent for parent in filtered_parents 
#                               if parent.get('year') and extract_year_value(parent.get('year')) >= from_year_int]
#         except (ValueError, AttributeError):
#             # Handle invalid year format
#             pass
    
#     if to_year:
#         try:
#             to_year_int = int(to_year.split('-')[0])  # Extract first year from "YYYY-YYYY" format
#             filtered_parents = [parent for parent in filtered_parents 
#                               if parent.get('year') and extract_year_value(parent.get('year')) <= to_year_int]
#         except (ValueError, AttributeError):
#             # Handle invalid year format
#             pass
    
#     if selected_options:
#         filtered_parents = [parent for parent in filtered_parents 
#                           if any(opt in (parent.get('participation') or '') for opt in selected_options)]
    
#     # Get parent IDs for child filtering
#     parent_ids = [parent.get('psk_id') for parent in filtered_parents]
    
#     # Filter children based on parent IDs
#     filtered_children = [child for child in all_children #                        if child.get('transaction_id') in parent_ids]
#     # Create mapping of parent ID to parent data for easy access
#     parent_map = {parent['psk_id']: parent for parent in filtered_parents}
    
#     # Add parent information to each child
#     for child in filtered_children:
#         parent_id = child.get('transaction_id')
#         if parent_id in parent_map:
#             child['parent_data'] = parent_map[parent_id]
    
#     # Handle export formats
#     if export_format:
#         if export_format.lower() == 'excel':
#             return export_to_excel(filtered_parents, filtered_children, selected_options)
#         elif export_format.lower() == 'pdf':
#             return export_to_pdf(filtered_parents, filtered_children, selected_options)
    
#     # Get unique staff IDs for dropdown
#     staff_ids = sorted(list(set(parent.get('stf_id') for parent in all_parents if parent.get('stf_id'))))
    
#     # Get unique years for dropdown (extract numeric values for sorting)
#     year_values = []
#     for parent in all_parents:
#         if parent.get('year'):
#             try:
#                 year_val = extract_year_value(parent.get('year'))
#                 year_values.append(year_val)
#             except (ValueError, AttributeError):
#                 continue
    
#     # Convert back to "YYYY-YYYY" format for display
#     years = sorted(list(set(f"{y}-{y+1}" for y in year_values)))
    
#     context = {
#         'parents': filtered_parents,
#         'children': filtered_children,
#         'staff_ids': staff_ids,
#         'years': years,
#         'options': PARTICIPATION_OPTIONS,
#         'selected_stf_id': stf_id,
#         'selected_from_year': from_year,
#         'selected_to_year': to_year,
#         'selected_options': selected_options,
#         'filter_applied': any([stf_id, from_year, to_year, selected_options])
#     }
    
#     return render(request, 'ParticipationFaculty_templates/filter_participations.html', context)

# def export_to_excel(parents, children, selected_options):
#     """
#     Export filtered data to Excel format
#     """
#     # Create DataFrames
#     parent_df = pd.DataFrame(parents)
#     child_df = pd.DataFrame(children)
    
#     # Create Excel writer
#     output = io.BytesIO()
#     with pd.ExcelWriter(output, engine='openpyxl') as writer:
#         # Write parent data
#         if not parent_df.empty:
#             parent_df.to_excel(writer, sheet_name='Parent Participations', index=False)
        
#         # Write child data
#         if not child_df.empty:
#             child_df.to_excel(writer, sheet_name='Child Participations', index=False)
        
#         # Write summary sheet
#         summary_data = {
#             'Total Parents': [len(parents)],
#             'Total Children': [len(children)],
#             'Selected Options': [', '.join(selected_options) if selected_options else 'All'],
#             'Export Date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
#         }
#         summary_df = pd.DataFrame(summary_data)
#         summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
#     output.seek(0)
    
#     # Create HTTP response
#     response = HttpResponse(
#         output.getvalue(),
#         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     )
#     response['Content-Disposition'] = 'attachment; filename="participations_filtered.xlsx"'
    
#     return response

# def export_to_pdf(parents, children, selected_options):
#     """
#     Export filtered data to PDF format
#     """
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="participations_filtered.pdf"'
    
#     doc = SimpleDocTemplate(response, pagesize=letter)
#     elements = []
#     styles = getSampleStyleSheet()
    
#     # Title
#     title_style = ParagraphStyle(
#         'CustomTitle',
#         parent=styles['Heading1'],
#         fontSize=16,
#         spaceAfter=30,
#         alignment=1  # Center
#     )
#     elements.append(Paragraph("Faculty Participation Report", title_style))
    
#     # Summary
#     summary_text = f"""
#     <b>Report Summary:</b><br/>
#     Total Parent Records: {len(parents)}<br/>
#     Total Child Records: {len(children)}<br/>
#     Selected Options: {', '.join(selected_options) if selected_options else 'All'}<br/>
#     Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#     """
#     elements.append(Paragraph(summary_text, styles['Normal']))
#     elements.append(Spacer(1, 20))
    
#     # Define consistent column widths for both tables
#     parent_col_widths = [80, 150, 120, 80, 130]  # Consistent widths for both tables
#     child_col_widths = [70, 100, 140, 200, 50]  # Consistent widths for both tables
    
#     # Parent Data Table
#     if parents:
#         elements.append(Paragraph("<b>Parent Participations</b>", styles['Heading2']))
#         parent_data = [['Staff ID', 'Name', 'Department', 'Academic Year', 'Participation Types']]
        
#         for parent in parents:
#             # Format academic year - FIXED: This should be inside the main loop
#             year_value = parent.get('year', '')
#             academic_year = ''
#             if year_value:
#                 try:
#                     if isinstance(year_value, str) and '-' in year_value:
#                         academic_year = year_value
#                     else:
#                         year_int = int(year_value)
#                         academic_year = f"{year_int}-{year_int + 1}"
#                 except (ValueError, TypeError):
#                     academic_year = str(year_value)
            
#             # Convert all values to strings before passing to Paragraph
#             parent_data.append([
#                 Paragraph(str(parent.get('stf_id', '')), styles['Normal']),
#                 Paragraph(str(parent.get('stf_name', '')), styles['Normal']),
#                 Paragraph(str(parent.get('department', '')), styles['Normal']),
#                 Paragraph(str(academic_year), styles['Normal']),  # Use the formatted academic_year
#                 Paragraph(str(parent.get('participation', '')), styles['Normal'])
#             ])
        
#         parent_table = Table(parent_data, colWidths=parent_col_widths, repeatRows=1)
#         parent_table.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('FONTSIZE', (0, 0), (-1, 0), 9),
#             ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#             ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#             ('GRID', (0, 0), (-1, -1), 1, colors.black),
#             ('FONTSIZE', (0, 1), (-1, -1), 8),
#             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#             ('LEFTPADDING', (0, 0), (-1, -1), 4),
#             ('RIGHTPADDING', (0, 0), (-1, -1), 4),
#             ('WORDWRAP', (0, 0), (-1, -1), True),
#         ]))
#         elements.append(parent_table)
#         elements.append(Spacer(1, 20))
    
#     # Child Data Table
#     if children:
#         elements.append(Paragraph("<b>Child Participations</b>", styles['Heading2']))
        
#         child_data = [['Parent Staff ID', 'Activity Type', 'Institution', 'Details', 'Attachment']]
        
#         for child in children:
#             # Determine activity type based on filled fields
#             activity_type = 'Unknown'
#             institution = ''
#             details = ''
            
#             if child.get('board_university_college_name'):
#                 activity_type = 'Board of Studies'
#                 institution = child.get('board_university_college_name', '')
#                 details = child.get('board_designation', '')
#             elif child.get('qp_university_college_name'):
#                 activity_type = 'Question Paper Setting'
#                 institution = child.get('qp_university_college_name', '')
#                 details = child.get('qp_subject', '')
#             elif child.get('eval_university_college_name'):
#                 activity_type = 'Evaluation'
#                 institution = child.get('eval_university_college_name', '')
#                 details = child.get('eval_subject', '')
#             elif child.get('design_development_university_college_name'):
#                 activity_type = 'Add-On Program'
#                 institution = child.get('design_development_university_college_name', '')
#                 details = child.get('design_development_addon', '')
#             elif child.get('certificate_university_college_name'):
#                 activity_type = 'Certificate Courses'
#                 institution = child.get('certificate_university_college_name', '')
#                 details = child.get('certificate_course', '')
#             elif child.get('external_examiner_university_college_name'):
#                 activity_type = 'External Examiner'
#                 institution = child.get('external_examiner_university_college_name', '')
#                 details = 'External Examiner'
#             elif child.get('conference_university_college_name'):
#                 activity_type = 'Conference'
#                 institution = child.get('conference_university_college_name', '')
#                 details = child.get('conference_name', '')
#             elif child.get('seminar_university_college_name'):
#                 activity_type = 'Seminar'
#                 institution = child.get('seminar_university_college_name', '')
#                 details = child.get('seminar_name', '')
#             elif child.get('workshop_university_college_name'):
#                 activity_type = 'Workshop'
#                 institution = child.get('workshop_university_college_name', '')
#                 details = child.get('workshop_name', '')
#             elif child.get('name_of_the_resource_person'):
#                 activity_type = 'FDP'
#                 institution = child.get('name_of_the_resource_person', '')
#                 details = child.get('name_of_the_program', '')
            
#             # Format dates
#             date_from = child.get('date_from', '')
#             date_to = child.get('date_to', '')
#             dates = f"{date_from} to {date_to}" if date_from and date_to else date_from or date_to or 'N/A'
            
#             # Convert all values to strings before passing to Paragraph
#             parent_staff_id = child.get('parent_data', {}).get('stf_id', '') if 'parent_data' in child else ''
            
#             child_data.append([
#                 Paragraph(str(parent_staff_id), styles['Normal']),
#                 Paragraph(str(activity_type), styles['Normal']),
#                 Paragraph(str(institution), styles['Normal']),
#                 Paragraph(str(details), styles['Normal']),
#                 Paragraph(str(dates), styles['Normal'])
#             ])
        
#         # Use the SAME column widths as parent table
#         child_table = Table(child_data, colWidths=child_col_widths, repeatRows=1)
#         child_table.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('FONTSIZE', (0, 0), (-1, 0), 9),
#             ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#             ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#             ('GRID', (0, 0), (-1, -1), 1, colors.black),
#             ('FONTSIZE', (0, 1), (-1, -1), 8),
#             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#             ('LEFTPADDING', (0, 0), (-1, -1), 4),
#             ('RIGHTPADDING', (0, 0), (-1, -1), 4),
#             ('WORDWRAP', (0, 0), (-1, -1), True),
#         ]))
#         elements.append(child_table)
    
#     # Build PDF
#     doc.build(elements)
#     return response

# Working Different Manner

# def export_to_excel(parents, children, selected_options):
#     """
#     Export filtered data to Excel format with clickable media file links and remove empty cells
#     """
#     # Prepare parent data for export - remove empty values
#     parent_data_for_export = []
#     for parent in parents:
#         parent_export = {k: v for k, v in parent.items() if v not in [None, '', []] and not pd.isna(v)}
#         parent_data_for_export.append(parent_export)
    
#     parent_df = pd.DataFrame(parent_data_for_export)
    
#     # Prepare child data for export - include media information with hyperlinks and remove empty values
#     child_data_for_export = []
#     for child in children:
#         child_export = child.copy()
        
#         # Extract media file information and create hyperlinks
#         media_files = child.get('media_files', [])
#         if media_files:
#             # Create hyperlinks for each media file
#             media_links = []
#             for media in media_files:
#                 file_name = media.get('file_name', 'Unknown')
#                 # Create the media URL using the provided format
#                 child_id = child.get('psk_id', '')
#                 if child_id:
#                     media_url = f"{API_STUDIO_URL}crudapp/view/media/naac01_faculty_participation_dc2_media/{child_id}"
#                     # Create Excel hyperlink formula
#                     hyperlink_formula = f'=HYPERLINK("{media_url}", "{file_name}")'
#                     media_links.append(hyperlink_formula)
#                 else:
#                     media_links.append(file_name)
            
#             # Join multiple links with newlines
#             child_export['media_files'] = "\n".join(media_links)
#         else:
#             child_export['media_files'] = "No media files"
        
#         # Remove parent_data to avoid circular references
#         if 'parent_data' in child_export:
#             del child_export['parent_data']
        
#         # Remove None values, empty strings, and empty lists
#         child_export = {k: v for k, v in child_export.items() if v not in [None, '', [], 'None', 'null'] and not pd.isna(v)}
        
#         child_data_for_export.append(child_export)
    
#     child_df = pd.DataFrame(child_data_for_export)
    
#     # Create Excel writer
#     output = io.BytesIO()
#     with pd.ExcelWriter(output, engine='openpyxl') as writer:
#         # Write parent data
#         if not parent_df.empty:
#             # Select only columns that have data
#             parent_columns_with_data = [col for col in parent_df.columns if not parent_df[col].isnull().all()]
#             if parent_columns_with_data:
#                 parent_df = parent_df[parent_columns_with_data]
#                 # Replace any remaining NaN values with empty strings
#                 parent_df = parent_df.fillna('')
#                 parent_df.to_excel(writer, sheet_name='Parent Participations', index=False)
        
#         # Write child data
#         if not child_df.empty:
#             # Select only columns that have data
#             child_columns_with_data = [col for col in child_df.columns if not child_df[col].isnull().all()]
#             if child_columns_with_data:
#                 child_df = child_df[child_columns_with_data]
#                 # Replace any remaining NaN values with empty strings
#                 child_df = child_df.fillna('')
#                 child_df.to_excel(writer, sheet_name='Child Participations', index=False)
        
#         # Write summary sheet
#         summary_data = {
#             'Total Parents': [len(parents)],
#             'Total Children': [len(children)],
#             'Selected Options': [', '.join(selected_options) if selected_options else 'All'],
#             'Export Date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
#         }
#         summary_df = pd.DataFrame(summary_data)
#         summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
#     output.seek(0)
    
#     # Create HTTP response
#     response = HttpResponse(
#         output.getvalue(),
#         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     )
#     response['Content-Disposition'] = 'attachment; filename="participations_filtered.xlsx"'
    
#     return response

# def export_to_excel(parents, children, selected_options):
#     """
#     Export filtered data to Excel format with clickable media file links
#     """
#     # Create DataFrames
#     parent_df = pd.DataFrame(parents)
    
#     # Prepare child data for export - include media information with hyperlinks
#     child_data_for_export = []
#     for child in children:
#         child_export = child.copy()
        
#         # Extract media file information and create hyperlinks
#         media_files = child.get('media_files', [])
#         if media_files:
#             # Create hyperlinks for each media file
#             media_links = []
#             for media in media_files:
#                 file_name = media.get('file_name', 'Unknown')
#                 # Create the media URL using the provided format
#                 child_id = child.get('psk_id', '')
#                 if child_id:
#                     media_url = f"{API_STUDIO_URL}crudapp/view/media/naac01_faculty_participation_dc2_media/{child_id}"
#                     # Create Excel hyperlink formula
#                     hyperlink_formula = f'=HYPERLINK("{media_url}", "{file_name}")'
#                     media_links.append(hyperlink_formula)
#                 else:
#                     media_links.append(file_name)
            
#             # Join multiple links with newlines
#             child_export['media_files'] = "\n".join(media_links)
#         else:
#             child_export['media_files'] = "No media files"
        
#         # Remove parent_data to avoid circular references
#         if 'parent_data' in child_export:
#             del child_export['parent_data']
        
#         # Remove None values and empty strings
#         child_export = {k: v for k, v in child_export.items() if v not in [None, '', []]}
        
#         child_data_for_export.append(child_export)
    
#     child_df = pd.DataFrame(child_data_for_export)
    
#     # Create Excel writer
#     output = io.BytesIO()
#     with pd.ExcelWriter(output, engine='openpyxl') as writer:
#         # Write parent data
#         if not parent_df.empty:
#             # Select and order specific columns for better readability
#             parent_columns = ['stf_id', 'stf_name', 'department', 'year', 'participation']
#             # Filter out None values
#             parent_df = parent_df[parent_columns] if all(col in parent_df.columns for col in parent_columns) else parent_df
#             parent_df = parent_df.where(pd.notnull(parent_df), None)
#             parent_df.to_excel(writer, sheet_name='Parent Participations', index=False)
        
#         # Write child data
#         if not child_df.empty:
#             # Select and order specific columns for better readability
#             child_columns = [
#                 'transaction_id', 'board_university_college_name', 'qp_university_college_name', 
#                 'eval_university_college_name', 'design_development_university_college_name',
#                 'certificate_university_college_name', 'external_examiner_university_college_name',
#                 'conference_university_college_name', 'seminar_university_college_name',
#                 'workshop_university_college_name', 'name_of_the_resource_person',
#                 'date_from', 'date_to', 'media_files'
#             ]
            
#             # Only include columns that exist in the DataFrame and have data
#             available_columns = [col for col in child_columns if col in child_df.columns and not child_df[col].isnull().all()]
            
#             # Add other columns that might have data
#             additional_columns = [col for col in child_df.columns if col not in child_columns and not child_df[col].isnull().all()]
            
#             # Combine all columns with data
#             all_columns = available_columns + additional_columns
            
#             if all_columns:
#                 child_df = child_df[all_columns]
#                 # Replace NaN values with empty strings
#                 child_df = child_df.fillna('')
#                 child_df.to_excel(writer, sheet_name='Child Participations', index=False)
        
#         # Write summary sheet
#         summary_data = {
#             'Total Parents': [len(parents)],
#             'Total Children': [len(children)],
#             'Selected Options': [', '.join(selected_options) if selected_options else 'All'],
#             'Export Date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
#         }
#         summary_df = pd.DataFrame(summary_data)
#         summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
#     output.seek(0)
    
#     # Create HTTP response
#     response = HttpResponse(
#         output.getvalue(),
#         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     )
#     response['Content-Disposition'] = 'attachment; filename="participations_filtered.xlsx"'
    
#     return response

# def export_to_pdf(parents, children, selected_options):
#     """
#     Export filtered data to PDF format with media file information
#     """
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="participations_filtered.pdf"'
    
#     doc = SimpleDocTemplate(response, pagesize=letter)
#     elements = []
#     styles = getSampleStyleSheet()
    
#     # Title
#     title_style = ParagraphStyle(
#         'CustomTitle',
#         parent=styles['Heading1'],
#         fontSize=16,
#         spaceAfter=30,
#         alignment=1  # Center
#     )
#     elements.append(Paragraph("Faculty Participation Report", title_style))
    
#     # Summary
#     summary_text = f"""
#     <b>Report Summary:</b><br/>
#     Total Parent Records: {len(parents)}<br/>
#     Total Child Records: {len(children)}<br/>
#     Selected Options: {', '.join(selected_options) if selected_options else 'All'}<br/>
#     Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#     """
#     elements.append(Paragraph(summary_text, styles['Normal']))
#     elements.append(Spacer(1, 20))
    
#     # Define consistent column widths for both tables
#     parent_col_widths = [80, 150, 120, 80, 130]  # Consistent widths for both tables
#     child_col_widths = [70, 100, 140, 200, 50]  # Consistent widths for both tables
    
#     # Parent Data Table
#     if parents:
#         elements.append(Paragraph("<b>Parent Participations</b>", styles['Heading2']))
#         parent_data = [['Staff ID', 'Name', 'Department', 'Academic Year', 'Participation Types']]
        
#         for parent in parents:
#             # Format academic year - FIXED: This should be inside the main loop
#             year_value = parent.get('year', '')
#             academic_year = ''
#             if year_value:
#                 try:
#                     if isinstance(year_value, str) and '-' in year_value:
#                         academic_year = year_value
#                     else:
#                         year_int = int(year_value)
#                         academic_year = f"{year_int}-{year_int + 1}"
#                 except (ValueError, TypeError):
#                     academic_year = str(year_value)
            
#             # Convert all values to strings before passing to Paragraph
#             parent_data.append([
#                 Paragraph(str(parent.get('stf_id', '')), styles['Normal']),
#                 Paragraph(str(parent.get('stf_name', '')), styles['Normal']),
#                 Paragraph(str(parent.get('department', '')), styles['Normal']),
#                 Paragraph(str(academic_year), styles['Normal']),  # Use the formatted academic_year
#                 Paragraph(str(parent.get('participation', '')), styles['Normal'])
#             ])
        
#         parent_table = Table(parent_data, colWidths=parent_col_widths, repeatRows=1)
#         parent_table.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('FONTSIZE', (0, 0), (-1, 0), 9),
#             ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#             ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#             ('GRID', (0, 0), (-1, -1), 1, colors.black),
#             ('FONTSIZE', (0, 1), (-1, -1), 8),
#             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#             ('LEFTPADDING', (0, 0), (-1, -1), 4),
#             ('RIGHTPADDING', (0, 0), (-1, -1), 4),
#             ('WORDWRAP', (0, 0), (-1, -1), True),
#         ]))
#         elements.append(parent_table)
#         elements.append(Spacer(1, 20))
    
#     # Child Data Table
#     if children:
#         elements.append(Paragraph("<b>Child Participations</b>", styles['Heading2']))
        
#         # Updated table headers to include media files
#         child_data = [['Parent Staff ID', 'Activity Type', 'Institution', 'Details', 'Attachment', 'Media Files']]
        
#         for child in children:
#             # Determine activity type based on filled fields
#             activity_type = 'Unknown'
#             institution = ''
#             details = ''
            
#             if child.get('board_university_college_name'):
#                 activity_type = 'Board of Studies'
#                 institution = child.get('board_university_college_name', '')
#                 details = child.get('board_designation', '')
#             elif child.get('qp_university_college_name'):
#                 activity_type = 'Question Paper Setting'
#                 institution = child.get('qp_university_college_name', '')
#                 details = child.get('qp_subject', '')
#             elif child.get('eval_university_college_name'):
#                 activity_type = 'Evaluation'
#                 institution = child.get('eval_university_college_name', '')
#                 details = child.get('eval_subject', '')
#             elif child.get('design_development_university_college_name'):
#                 activity_type = 'Add-On Program'
#                 institution = child.get('design_development_university_college_name', '')
#                 details = child.get('design_development_addon', '')
#             elif child.get('certificate_university_college_name'):
#                 activity_type = 'Certificate Courses'
#                 institution = child.get('certificate_university_college_name', '')
#                 details = child.get('certificate_course', '')
#             elif child.get('external_examiner_university_college_name'):
#                 activity_type = 'External Examiner'
#                 institution = child.get('external_examiner_university_college_name', '')
#                 details = 'External Examiner'
#             elif child.get('conference_university_college_name'):
#                 activity_type = 'Conference'
#                 institution = child.get('conference_university_college_name', '')
#                 details = child.get('conference_name', '')
#             elif child.get('seminar_university_college_name'):
#                 activity_type = 'Seminar'
#                 institution = child.get('seminar_university_college_name', '')
#                 details = child.get('seminar_name', '')
#             elif child.get('workshop_university_college_name'):
#                 activity_type = 'Workshop'
#                 institution = child.get('workshop_university_college_name', '')
#                 details = child.get('workshop_name', '')
#             elif child.get('name_of_the_resource_person'):
#                 activity_type = 'FDP'
#                 institution = child.get('name_of_the_resource_person', '')
#                 details = child.get('name_of_the_program', '')
            
#             # Format dates
#             date_from = child.get('date_from', '')
#             date_to = child.get('date_to', '')
#             dates = f"{date_from} to {date_to}" if date_from and date_to else date_from or date_to or 'N/A'
            
#             # Get media files information
#             media_files = child.get('media_files', [])
#             media_info = "No media files"
#             if media_files:
#                 media_names = [media.get('file_name', 'Unknown') for media in media_files]
#                 media_info = ", ".join(media_names)
            
#             # Convert all values to strings before passing to Paragraph
#             parent_staff_id = child.get('parent_data', {}).get('stf_id', '') if 'parent_data' in child else ''
            
#             child_data.append([
#                 Paragraph(str(parent_staff_id), styles['Normal']),
#                 Paragraph(str(activity_type), styles['Normal']),
#                 Paragraph(str(institution), styles['Normal']),
#                 Paragraph(str(details), styles['Normal']),
#                 Paragraph(str(dates), styles['Normal']),
#                 Paragraph(str(media_info), styles['Normal'])
#             ])
        
#         # Adjust column widths to accommodate the new Media Files column
#         child_col_widths = [70, 100, 120, 150, 50, 100]
        
#         child_table = Table(child_data, colWidths=child_col_widths, repeatRows=1)
#         child_table.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('FONTSIZE', (0, 0), (-1, 0), 9),
#             ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#             ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#             ('GRID', (0, 0), (-1, -1), 1, colors.black),
#             ('FONTSIZE', (0, 1), (-1, -1), 8),
#             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#             ('LEFTPADDING', (0, 0), (-1, -1), 4),
#             ('RIGHTPADDING', (0, 0), (-1, -1), 4),
#             ('WORDWRAP', (0, 0), (-1, -1), True),
#         ]))
#         elements.append(child_table)
    
#     # Build PDF
#     doc.build(elements)
#     return response

# Add these URL patterns to your urls.py:

# def filter_participations(request):
#     """
#     Main filtering function for participations with Excel and PDF export
#     """
#     # Get all parent participations
#     parent_url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc1/all"
#     parent_response = requests.get(parent_url)
    
#     if parent_response.status_code != 200:
#         return HttpResponse("Error fetching participation data")
    
#     all_parents = parent_response.json()
    
#     # Get all child participations
#     child_url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc2/all"
#     child_response = requests.get(child_url)
    
#     all_children = child_response.json() if child_response.status_code == 200 else []
    
#     # Get filter parameters from request
#     stf_id = request.GET.get('stf_id', '').strip()
#     from_year = request.GET.get('from_year', '').strip()
#     to_year = request.GET.get('to_year', '').strip()
#     selected_options = request.GET.getlist('options')
#     export_format = request.GET.get('export', '')
    
#     # Filter parents
#     filtered_parents = all_parents
    
#     if stf_id:
#         filtered_parents = [parent for parent in filtered_parents if parent.get('stf_id') == stf_id]
    
#     # Convert year values to integers for comparison
#     if from_year:
#         try:
#             from_year_int = int(from_year.split('-')[0])  # Extract first year from "YYYY-YYYY" format
#             filtered_parents = [parent for parent in filtered_parents if parent.get('year') and extract_year_value(parent.get('year')) >= from_year_int]
#         except (ValueError, AttributeError):
#             # Handle invalid year format
#             pass
    
#     if to_year:
#         try:
#             to_year_int = int(to_year.split('-')[0])  # Extract first year from "YYYY-YYYY" format
#             filtered_parents = [parent for parent in filtered_parents if parent.get('year') and extract_year_value(parent.get('year')) <= to_year_int]
#         except (ValueError, AttributeError):
#             # Handle invalid year format
#             pass
    
#     if selected_options:
#         filtered_parents = [parent for parent in filtered_parents if any(opt in (parent.get('participation') or '') for opt in selected_options)]
    
#     # Get parent IDs for child filtering
#     parent_ids = [parent.get('psk_id') for parent in filtered_parents]
    
#     # Filter children based on parent IDs
#     filtered_children = [child for child in all_children if child.get('transaction_id') in parent_ids]
#     # Fetch media files for each child
#     for child in filtered_children:
#         child_id = child.get('psk_id')
#         media_url = f"{API_STUDIO_URL}crudapp/get/media/naac01_faculty_participation_dc2_media/parent/{child_id}"
#         media_response = requests.get(media_url)
        
#         if media_response.status_code == 200:
#             media_data = media_response.json()
#             child['media_files'] = media_data
#         else:
#             child['media_files'] = []
    
#     # Create mapping of parent ID to parent data for easy access
#     parent_map = {parent['psk_id']: parent for parent in filtered_parents}
    
#     # Add parent information to each child
#     for child in filtered_children:
#         parent_id = child.get('transaction_id')
#         if parent_id in parent_map:
#             child['parent_data'] = parent_map[parent_id]
    
#     # Handle export formats
#     if export_format:
#         if export_format.lower() == 'excel':
#             return export_to_excel(filtered_parents, filtered_children, selected_options)
#         elif export_format.lower() == 'pdf':
#             return export_to_pdf(filtered_parents, filtered_children, selected_options)
    
#     # Get unique staff IDs for dropdown
#     staff_ids = sorted(list(set(parent.get('stf_id') for parent in all_parents if parent.get('stf_id'))))
    
#     # Get unique years for dropdown (extract numeric values for sorting)
#     year_values = []
#     for parent in all_parents:
#         if parent.get('year'):
#             try:
#                 year_val = extract_year_value(parent.get('year'))
#                 year_values.append(year_val)
#             except (ValueError, AttributeError):
#                 continue
    
#     # Convert back to "YYYY-YYYY" format for display
#     years = sorted(list(set(f"{y}-{y+1}" for y in year_values)))
    
#     context = {
#         'parents': filtered_parents,
#         'children': filtered_children,
#         'staff_ids': staff_ids,
#         'years': years,
#         'options': PARTICIPATION_OPTIONS,
#         'selected_stf_id': stf_id,
#         'selected_from_year': from_year,
#         'selected_to_year': to_year,
#         'selected_options': selected_options,
#         'filter_applied': any([stf_id, from_year, to_year, selected_options])
#     }
    
#     return render(request, 'ParticipationFaculty_templates/filter_participations.html', context)

# def extract_year_value(year_str):
#     """
#     Extract numeric year value from academic year string format "YYYY-YYYY"
#     Returns the first year as integer
#     """
#     if not year_str:
#         return None
    
#     # Handle different year formats
#     if isinstance(year_str, int):
#         return year_str
    
#     if isinstance(year_str, str):
#         # Handle "YYYY-YYYY" format
#         if '-' in year_str:
#             try:
#                 return int(year_str.split('-')[0])
#             except (ValueError, IndexError):
#                 return None
#         # Handle single year "YYYY"
#         else:
#             try:
#                 return int(year_str)
#             except ValueError:
#                 return None
    
#     return None

# Import your required functions (adjust these imports based on your project structure)
# from .utils import research_key, get_research_data, get_settings, roles_tbl
# from .constants import API_STUDIO_URL, PARTICIPATION_OPTIONS
# Keep the extract_year_value, export_to_excel, and export_to_pdf functions as they are


"""
path('participations/filter/', filter_participations, name='filter_participations'),
"""
       
# import pandas as pd

import io
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import json
from datetime import datetime

# def filter_participations(request, research_key, get_research_data):
#     """
#     Main filtering function for participations with Excel and PDF export
#     with role-based access control (Staff vs HOD)
#     """
#     # Step 1: Get the logged-in username
#     user = get_settings(request)
#     username = user.get('username', '')
#     username = 'CS-T151'
    
#     # Step 2: Determine user role (Staff or HOD)
#     role_url = f"{API_STUDIO_URL}getapi/asa0504_01_01"
#     payload = json.dumps({"queries": [{"field": "username", "value": username, "operation": "equal"}], "search_type": "first"})
#     role_response = requests.post(role_url, headers={'Content-Type': 'application/json'}, data=payload)
#     value_user = int(role_response.json().get("user_roles", "0").strip("{}")) if role_response.status_code == 200 else 0

#     role_list = roles_tbl(request)
#     user_role = next((role.get("user_role") for role in role_list if role.get("psk_id") == value_user), "Staff")
    
#     # Step 3: Get research data to determine department for HOD
#     access_token, token_type = research_key()
#     research_data = get_research_data(access_token, token_type)
#     staff_info = next((s for s in research_data if s.get("stf_id") == username), {})
#     department_name = staff_info.get("department", "")
    
#     # Get all parent participations
#     parent_url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc1/all"
#     parent_response = requests.get(parent_url)
    
#     if parent_response.status_code != 200:
#         return HttpResponse("Error fetching participation data")
    
#     all_parents = parent_response.json()
    
#     # Get all child participations
#     child_url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc2/all"
#     child_response = requests.get(child_url)
    
#     all_children = child_response.json() if child_response.status_code == 200 else []
    
#     # Get filter parameters from request
#     stf_id = request.GET.get('stf_id', '').strip()
#     from_year = request.GET.get('from_year', '').strip()
#     to_year = request.GET.get('to_year', '').strip()
#     selected_options = request.GET.getlist('options')
#     export_format = request.GET.get('export', '')
    
#     # ROLE-BASED FILTERING: Apply department filter for HOD
#     if user_role == "Hod" and not stf_id:
#         # HOD can only see staff from their own department
#         department_staff = [s for s in research_data if s.get("department") == department_name]
#         dept_staff_ids = [s.get("stf_id") for s in department_staff]
        
#         # Filter parents to only those in HOD's department
#         all_parents = [parent for parent in all_parents if parent.get('stf_id') in dept_staff_ids]
    
#     # Filter parents based on user selections
#     filtered_parents = all_parents
    
#     if stf_id:
#         # If specific staff ID is selected, apply that filter
#         filtered_parents = [parent for parent in filtered_parents if parent.get('stf_id') == stf_id]
#     elif user_role == "Staff":
#         # Staff can only see their own data unless they select someone else
#         filtered_parents = [parent for parent in filtered_parents if parent.get('stf_id') == username]
    
#     # Convert year values to integers for comparison
#     if from_year:
#         try:
#             from_year_int = int(from_year.split('-')[0])
#             filtered_parents = [parent for parent in filtered_parents if parent.get('year') and extract_year_value(parent.get('year')) >= from_year_int]
#         except (ValueError, AttributeError):
#             pass
    
#     if to_year:
#         try:
#             to_year_int = int(to_year.split('-')[0])
#             filtered_parents = [parent for parent in filtered_parents if parent.get('year') and extract_year_value(parent.get('year')) <= to_year_int]
#         except (ValueError, AttributeError):
#             pass
    
#     if selected_options:
#         filtered_parents = [parent for parent in filtered_parents if any(opt in (parent.get('participation') or '') for opt in selected_options)]
    
#     # Get parent IDs for child filtering
#     parent_ids = [parent.get('psk_id') for parent in filtered_parents]
    
#     # Filter children based on parent IDs
#     filtered_children = [child for child in all_children if child.get('transaction_id') in parent_ids]
    
#     # Fetch media files for each child
#     for child in filtered_children:
#         child_id = child.get('psk_id')
#         media_url = f"{API_STUDIO_URL}crudapp/get/media/naac01_faculty_participation_dc2_media/parent/{child_id}"
#         media_response = requests.get(media_url)
        
#         if media_response.status_code == 200:
#             media_data = media_response.json()
#             child['media_files'] = media_data
#         else:
#             child['media_files'] = []
    
#     # Create mapping of parent ID to parent data for easy access
#     parent_map = {parent['psk_id']: parent for parent in filtered_parents}
    
#     # Add parent information to each child
#     for child in filtered_children:
#         parent_id = child.get('transaction_id')
#         if parent_id in parent_map:
#             child['parent_data'] = parent_map[parent_id]
    
#     # Handle export formats
#     if export_format:
#         if export_format.lower() == 'excel':
#             return export_to_excel(filtered_parents, filtered_children, selected_options)
#         elif export_format.lower() == 'pdf':
#             return export_to_pdf(filtered_parents, filtered_children, selected_options)
    
#     # Get unique staff IDs for dropdown - filtered by role
#     if user_role == "Hod":
#         # HOD can see all staff in their department
#         staff_ids = sorted(list(set(parent.get('stf_id') for parent in all_parents if parent.get('stf_id') in dept_staff_ids)))
#     else:
#         # Staff can only see themselves
#         staff_ids = [username]
    
#     # Get unique years for dropdown
#     year_values = []
#     for parent in all_parents:
#         if parent.get('year'):
#             try:
#                 year_val = extract_year_value(parent.get('year'))
#                 year_values.append(year_val)
#             except (ValueError, AttributeError):
#                 continue
    
#     # Convert back to "YYYY-YYYY" format for display
#     years = sorted(list(set(f"{y}-{y+1}" for y in year_values)))
    
#     context = {'parents': filtered_parents,'children': filtered_children,'staff_ids': staff_ids,'years': years,'options': PARTICIPATION_OPTIONS,'selected_stf_id': stf_id,'selected_from_year': from_year,'selected_to_year': to_year,'selected_options': selected_options,'filter_applied': any([stf_id, from_year, to_year, selected_options]),'user_role': user_role,'username': username}
    
#     return render(request, 'ParticipationFaculty_templates/filter_participations.html', context)

# views.py
import pandas as pd
import io
import requests
import json
from django.http import HttpResponse
from django.shortcuts import render
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime

def filter_participations(request):
    """
    Main filtering function for participations with Excel and PDF export
    with role-based access control (Staff vs HOD)
    """
    # Step 1: Get the logged-in username
    user = get_settings(request)
    username = user.get('username', '')
    # username = 'CS-T151'  # Remove this hardcoded value in production
    
    # Step 2: Determine user role (Staff or HOD)
    role_url = f"{API_STUDIO_URL}getapi/asa0504_01_01"
    payload = json.dumps({
        "queries": [{"field": "username", "value": username, "operation": "equal"}],
        "search_type": "first"
    })
    role_response = requests.post(role_url, headers={'Content-Type': 'application/json'}, data=payload)
    value_user = int(role_response.json().get("user_roles", "0").strip("{}")) if role_response.status_code == 200 else 0

    role_list = roles_tbl(request)
    user_role = next((role.get("user_role") for role in role_list if role.get("psk_id") == value_user), "Staff")
    
    # Step 3: Get research data to determine department for HOD
    access_token, token_type = faculty_auth()
    research_data = faculty_token(access_token, token_type)
    staff_info = next((s for s in research_data if s.get("stf_id") == username), {})
    department_name = staff_info.get("department", "")
    
    # Get all parent participations
    parent_url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc1/all"
    parent_response = requests.get(parent_url)
    
    if parent_response.status_code != 200:
        return HttpResponse("Error fetching participation data")
    
    all_parents = parent_response.json()
    
    # Get all child participations
    child_url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc2/all"
    child_response = requests.get(child_url)
    
    all_children = child_response.json() if child_response.status_code == 200 else []
    
    # Get filter parameters from request
    stf_id = request.GET.get('stf_id', '').strip()
    from_year = request.GET.get('from_year', '').strip()
    to_year = request.GET.get('to_year', '').strip()
    selected_options = request.GET.getlist('options')
    export_format = request.GET.get('export', '')
    
    # ROLE-BASED FILTERING: Apply department filter for HOD
    if user_role == "Hod" and not stf_id:
        # HOD can only see staff from their own department
        department_staff = [s for s in research_data if s.get("department") == department_name]
        dept_staff_ids = [s.get("stf_id") for s in department_staff]
        
        # Filter parents to only those in HOD's department
        all_parents = [parent for parent in all_parents if parent.get('stf_id') in dept_staff_ids]
    
    # Filter parents based on user selections
    filtered_parents = all_parents
    
    if stf_id:
        # If specific staff ID is selected, apply that filter
        filtered_parents = [parent for parent in filtered_parents if parent.get('stf_id') == stf_id]
    elif user_role == "Staff":
        # Staff can only see their own data unless they select someone else
        filtered_parents = [parent for parent in filtered_parents if parent.get('stf_id') == username]
    
    # Convert year values to integers for comparison
    if from_year:
        try:
            from_year_int = int(from_year.split('-')[0])
            filtered_parents = [parent for parent in filtered_parents if parent.get('year') and extract_year_value(parent.get('year')) >= from_year_int]
        except (ValueError, AttributeError):
            pass
    
    if to_year:
        try:
            to_year_int = int(to_year.split('-')[0])
            filtered_parents = [parent for parent in filtered_parents if parent.get('year') and extract_year_value(parent.get('year')) <= to_year_int]
        except (ValueError, AttributeError):
            pass
    
    if selected_options:
        filtered_parents = [parent for parent in filtered_parents if any(opt in (parent.get('participation') or '') for opt in selected_options)]
    
    # Get parent IDs for child filtering
    parent_ids = [parent.get('psk_id') for parent in filtered_parents]
    
    # Filter children based on parent IDs
    filtered_children = [child for child in all_children if child.get('transaction_id') in parent_ids]
    
    # Fetch media files for each child
    for child in filtered_children:
        child_id = child.get('psk_id')
        media_url = f"{API_STUDIO_URL}crudapp/get/media/naac01_faculty_participation_dc2_media/parent/{child_id}"
        media_response = requests.get(media_url)
        
        if media_response.status_code == 200:
            media_data = media_response.json()
            child['media_files'] = media_data
        else:
            child['media_files'] = []
    
    # Create mapping of parent ID to parent data for easy access
    parent_map = {parent['psk_id']: parent for parent in filtered_parents}
    
    # Add parent information to each child
    for child in filtered_children:
        parent_id = child.get('transaction_id')
        if parent_id in parent_map:
            child['parent_data'] = parent_map[parent_id]
    
    # Handle export formats
    if export_format:
        if export_format.lower() == 'excel':
            return export_to_excel(filtered_parents, filtered_children, selected_options)
        elif export_format.lower() == 'pdf':
            return export_to_pdf(filtered_parents, filtered_children, selected_options)
    
    # Get unique staff IDs for dropdown - filtered by role
    if user_role == "Hod":
        # HOD can see all staff in their department
        department_staff = [s for s in research_data if s.get("department") == department_name]
        dept_staff_ids = [s.get("stf_id") for s in department_staff]
        staff_ids = sorted(list(set(parent.get('stf_id') for parent in all_parents if parent.get('stf_id') in dept_staff_ids)))
    else:
        # Staff can only see themselves
        staff_ids = [username]
    
    # Get unique years for dropdown
    year_values = []
    for parent in all_parents:
        if parent.get('year'):
            try:
                year_val = extract_year_value(parent.get('year'))
                year_values.append(year_val)
            except (ValueError, AttributeError):
                continue
    
    # Convert back to "YYYY-YYYY" format for display
    years = sorted(list(set(f"{y}-{y+1}" for y in year_values)))
    
    context = {
        'parents': filtered_parents,
        'children': filtered_children,
        'staff_ids': staff_ids,
        'years': years,
        'options': PARTICIPATION_OPTIONS,
        'selected_stf_id': stf_id,
        'selected_from_year': from_year,
        'selected_to_year': to_year,
        'selected_options': selected_options,
        'filter_applied': any([stf_id, from_year, to_year, selected_options]),
        'user_role': user_role,
        'username': username
    }
    
    return render(request, 'ParticipationFaculty_templates/filter_participations.html', context)

def extract_year_value(year_str):
    """Extract first year from academic year string or return None"""
    try:
        return int(str(year_str).split('-')[0]) if year_str else None
    except:
        return None

def export_to_excel(parents, children, selected_options):
    """
    Export filtered data to Excel format with formatted child participations
    """
    # Prepare parent data for export - remove empty values
    parent_data_for_export = []
    for parent in parents:
        parent_export = {k: v for k, v in parent.items() if v not in [None, '', []] and not pd.isna(v)}
        parent_data_for_export.append(parent_export)
    
    parent_df = pd.DataFrame(parent_data_for_export)
    
    # Prepare child data in the specific format requested
    child_data_for_export = []
    for child in children:
        # Get parent staff ID
        parent_staff_id = child.get('parent_data', {}).get('stf_id', '') if 'parent_data' in child else ''
        
        # Determine activity type based on filled fields
        activity_type = 'Unknown'
        institution = ''
        details = ''
        
        if child.get('board_university_college_name'):
            activity_type = 'Board of Studies'
            institution = child.get('board_university_college_name', '')
            details = child.get('board_designation', '')
        elif child.get('qp_university_college_name'):
            activity_type = 'Question Paper Setting'
            institution = child.get('qp_university_college_name', '')
            details = child.get('qp_subject', '')
        elif child.get('eval_university_college_name'):
            activity_type = 'Evaluation'
            institution = child.get('eval_university_college_name', '')
            details = child.get('eval_subject', '')
        elif child.get('design_development_university_college_name'):
            activity_type = 'Add-On Program'
            institution = child.get('design_development_university_college_name', '')
            details = child.get('design_development_addon', '')
        elif child.get('certificate_university_college_name'):
            activity_type = 'Certificate Courses'
            institution = child.get('certificate_university_college_name', '')
            details = child.get('certificate_course', '')
        elif child.get('external_examiner_university_college_name'):
            activity_type = 'External Examiner'
            institution = child.get('external_examiner_university_college_name', '')
            details = 'External Examiner'
        elif child.get('conference_university_college_name'):
            activity_type = 'Conference'
            institution = child.get('conference_university_college_name', '')
            details = child.get('conference_name', '')
        elif child.get('seminar_university_college_name'):
            activity_type = 'Seminar'
            institution = child.get('seminar_university_college_name', '')
            details = child.get('seminar_name', '')
        elif child.get('workshop_university_college_name'):
            activity_type = 'Workshop'
            institution = child.get('workshop_university_college_name', '')
            details = child.get('workshop_name', '')
        elif child.get('name_of_the_resource_person'):
            activity_type = 'FDP'
            institution = child.get('name_of_the_resource_person', '')
            details = child.get('name_of_the_program', '')
        
        # Get media files information and create hyperlinks
        media_files = child.get('media_files', [])
        attachment = "No media files"
        
        if media_files:
            # Create hyperlinks for each media file
            media_links = []
            for media in media_files:
                file_name = media.get('file_name', 'Unknown')
                # Create the media URL using the provided format
                child_id = child.get('psk_id', '')
                if child_id:
                    media_url = f"{API_STUDIO_URL}crudapp/view/media/naac01_faculty_participation_dc2_media/{child_id}"
                    # Create Excel hyperlink formula
                    hyperlink_formula = f'=HYPERLINK("{media_url}", "{file_name}")'
                    media_links.append(hyperlink_formula)
                else:
                    media_links.append(file_name)
            
            # Join multiple links with newlines
            attachment = "\n".join(media_links)
        
        # Create the formatted child data
        child_export = {
            'Parent Staff ID': parent_staff_id,
            'Activity Type': activity_type,
            'Institution': institution,
            'Details': details,
            'Attachment': attachment
        }
        
        # Remove empty values
        child_export = {k: v for k, v in child_export.items() if v not in [None, '', [], 'None', 'null'] and not pd.isna(v)}
        
        child_data_for_export.append(child_export)
    
    child_df = pd.DataFrame(child_data_for_export)
    
    # Create Excel writer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write parent data
        if not parent_df.empty:
            # Select only columns that have data
            parent_columns_with_data = [col for col in parent_df.columns if not parent_df[col].isnull().all()]
            if parent_columns_with_data:
                parent_df = parent_df[parent_columns_with_data]
                # Replace any remaining NaN values with empty strings
                parent_df = parent_df.fillna('')
                parent_df.to_excel(writer, sheet_name='Parent Participations', index=False)
        
        # Write child data
        if not child_df.empty:
            # Ensure we have the correct column order
            desired_columns = ['Parent Staff ID', 'Activity Type', 'Institution', 'Details', 'Attachment']
            available_columns = [col for col in desired_columns if col in child_df.columns]
            
            # Add any additional columns that might exist
            additional_columns = [col for col in child_df.columns if col not in desired_columns]
            all_columns = available_columns + additional_columns
            
            if all_columns:
                child_df = child_df[all_columns]
                # Replace any remaining NaN values with empty strings
                child_df = child_df.fillna('')
                child_df.to_excel(writer, sheet_name='Child Participations', index=False)
                
                # ✅ Apply hyperlink style (blue + underline) to "Attachment" column
                worksheet = writer.sheets['Child Participations']
                attachment_col_idx = all_columns.index('Attachment') + 1  # Excel is 1-based
                hyperlink_font = Font(color="0000FF", underline="single")

                for row in range(2, len(child_df) + 2):  # skip header row
                    cell = worksheet.cell(row=row, column=attachment_col_idx)
                    if cell.value and cell.value.startswith("=HYPERLINK("):
                        cell.font = hyperlink_font
        
        # Write summary sheet
        summary_data = {
            'Total Parents': [len(parents)],
            'Total Children': [len(children)],
            'Selected Options': [', '.join(selected_options) if selected_options else 'All'],
            'Export Date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    
    # Create HTTP response
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="participations_filtered.xlsx"'
    
    return response

def export_to_pdf(parents, children, selected_options):
    """
    Export filtered data to PDF format with clickable media file links
    """
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="participations_filtered.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=12,
        spaceAfter=30,
        alignment=1  # Center
    )
    elements.append(Paragraph("Faculty Participation Report", title_style))
    
    # Summary
    summary_text = f"""
    <b>Report Summary:</b><br/>
    Total Parent Records: {len(parents)}<br/>
    Total Child Records: {len(children)}<br/>
    Selected Options: {', '.join(selected_options) if selected_options else 'All'}<br/>
    Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    elements.append(Paragraph(summary_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Define consistent column widths for both tables
    parent_col_widths = [80, 150, 120, 80, 130]
    child_col_widths = [70, 100, 120, 150, 150]
    
    # Parent Data Table
    if parents:
        elements.append(Paragraph("<b>Parent Participations</b>", styles['Heading2']))
        parent_data = [['Staff ID', 'Name', 'Department', 'Academic Year', 'Participation Types']]
        
        for parent in parents:
            # Format academic year
            year_value = parent.get('year', '')
            academic_year = ''
            if year_value:
                try:
                    if isinstance(year_value, str) and '-' in year_value:
                        academic_year = year_value
                    else:
                        year_int = int(year_value)
                        academic_year = f"{year_int}-{year_int + 1}"
                except (ValueError, TypeError):
                    academic_year = str(year_value)
            
            parent_data.append([
                Paragraph(str(parent.get('stf_id', '')), styles['Normal']),
                Paragraph(str(parent.get('stf_name', '')), styles['Normal']),
                Paragraph(str(parent.get('department', '')), styles['Normal']),
                Paragraph(str(academic_year), styles['Normal']),
                Paragraph(str(parent.get('participation', '')), styles['Normal'])
            ])
        
        parent_table = Table(parent_data, colWidths=parent_col_widths, repeatRows=1)
        parent_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        elements.append(parent_table)
        elements.append(Spacer(1, 20))
    
    # Child Data Table
    if children:
        elements.append(Paragraph("<b>Child Participations</b>", styles['Heading2']))
        
        # Updated table headers to include media files
        child_data = [['Parent Staff ID', 'Activity Type', 'Institution', 'Details', 'Attachment']]
        
        for child in children:
            # Determine activity type based on filled fields
            activity_type = 'Unknown'
            institution = ''
            details = ''
            
            if child.get('board_university_college_name'):
                activity_type = 'Board of Studies'
                institution = child.get('board_university_college_name', '')
                details = child.get('board_designation', '')
            elif child.get('qp_university_college_name'):
                activity_type = 'Question Paper Setting'
                institution = child.get('qp_university_college_name', '')
                details = child.get('qp_subject', '')
            elif child.get('eval_university_college_name'):
                activity_type = 'Evaluation'
                institution = child.get('eval_university_college_name', '')
                details = child.get('eval_subject', '')
            elif child.get('design_development_university_college_name'):
                activity_type = 'Add-On Program'
                institution = child.get('design_development_university_college_name', '')
                details = child.get('design_development_addon', '')
            elif child.get('certificate_university_college_name'):
                activity_type = 'Certificate Courses'
                institution = child.get('certificate_university_college_name', '')
                details = child.get('certificate_course', '')
            elif child.get('external_examiner_university_college_name'):
                activity_type = 'External Examiner'
                institution = child.get('external_examiner_university_college_name', '')
                details = 'External Examiner'
            elif child.get('conference_university_college_name'):
                activity_type = 'Conference'
                institution = child.get('conference_university_college_name', '')
                details = child.get('conference_name', '')
            elif child.get('seminar_university_college_name'):
                activity_type = 'Seminar'
                institution = child.get('seminar_university_college_name', '')
                details = child.get('seminar_name', '')
            elif child.get('workshop_university_college_name'):
                activity_type = 'Workshop'
                institution = child.get('workshop_university_college_name', '')
                details = child.get('workshop_name', '')
            elif child.get('name_of_the_resource_person'):
                activity_type = 'FDP'
                institution = child.get('name_of_the_resource_person', '')
                details = child.get('name_of_the_program', '')
            
            # Format dates
            date_from = child.get('date_from', '')
            date_to = child.get('date_to', '')
            dates = f"{date_from} to {date_to}" if date_from and date_to else date_from or date_to or 'N/A'
            
            # Get media files information and create clickable links
            media_files = child.get('media_files', [])
            media_links = []
            
            if media_files:
                for media in media_files:
                    file_name = media.get('file_name', 'Unknown')
                    # Create the media URL using the provided format
                    child_id = child.get('psk_id', '')
                    if child_id:
                        media_url = f"{API_STUDIO_URL}crudapp/view/media/naac01_faculty_participation_dc2_media/{child_id}"
                        # Create a clickable link with the filename as the visible text
                        link_text = f'<a href="{media_url}" color="blue"><u>{file_name}</u></a>'
                        media_links.append(link_text)
                    else:
                        media_links.append(f"{file_name} (No ID)")
                
                media_info = "<br/>".join(media_links)
            else:
                media_info = "No media files"
            
            # Convert all values to strings before passing to Paragraph
            parent_staff_id = child.get('parent_data', {}).get('stf_id', '') if 'parent_data' in child else ''
            
            child_data.append([
                Paragraph(str(parent_staff_id), styles['Normal']),
                Paragraph(str(activity_type), styles['Normal']),
                Paragraph(str(institution), styles['Normal']),
                Paragraph(str(details), styles['Normal']),
                # Paragraph(str(dates), styles['Normal']),
                Paragraph(media_info, styles['Normal'])  # This will render as clickable links
            ])
        
        child_table = Table(child_data, colWidths=child_col_widths, repeatRows=1)
        child_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        elements.append(child_table)
    
    # Build PDF
    doc.build(elements)
    return response

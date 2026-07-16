from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
import requests
import json
from datetime import datetime
from collections import Counter
from user_management.settings_views import get_settings
from MIS.functions import validate_file_format_faculty, validate_file_size

API_STUDIO_URL = "https://api.hcaschennai.edu.in/"

PARTICIPATION_OPTIONS = [
    'Board of Studies', 'Question Paper Setting', 'Evaluation', 
    'Add-On (Other University & College)', 'Certificate Courses',
    'External Examiner', 'Conference', 'Seminar', 'Workshop', 'Faculty Development Program'
]

def faculty_auth():
    url = "https://api.hcaschennai.edu.in/auth/token"
    payload = json.dumps({"secret_key": "C4ZoXbsAnHLjk1Xyz4QPT2eoiNx6K6fo"})
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        response_data = response.json()
        return response_data.get('access_token'), response_data.get('token_type')
    return None, None

def faculty_token(access_token, token_type):
    url = "https://api.hcaschennai.edu.in/sqlviews/api/v1/auth/get_response_data"
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
    username = user.get('username', '')
    # username = 'CS-T151'
    
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
    username = user.get('username', '')
    # username = 'CS-T151'
    
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
    username = user.get('username', '')
    # username = 'CS-T151'
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
        c.strip() for p in filtered_data for c in p.get("participation", "").split(",") if c.strip() in categories
    }

    counts = Counter(
        t.strip().replace(" ", "_") for p in filtered_data 
        for t in p.get("participation", "").split(",") if t.strip()
    )

    child_api = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc2/all"
    child_response = requests.get(child_api)
    if child_response.status_code != 200:
        return HttpResponse("Could not load child records")
    child_data = child_response.json()

    staff_psk_ids = {p.get("psk_id") for p in filtered_data}
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

        # --- fix: validate date fields properly ---
        date_from = request.POST.get('date_from')
        # date_from = f"{date_from.split('-')[2]}-{date_from.split('-')[1]}-{date_from.split('-')[0]}" if date_from and len(date_from.split('-')[0]) == 4 else (date_from if date_from and len(date_from.split('-')[2]) == 4 else "")
        date_to = request.POST.get('date_to')
        # date_to = f"{date_to.split('-')[2]}-{date_to.split('-')[1]}-{date_to.split('-')[0]}" if date_to and len(date_to.split('-')[0]) == 4 else (date_to if date_to and len(date_to.split('-')[2]) == 4 else "")

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
            'date_from': date_from if date_from else "",
            'date_to': date_to if date_to else "",
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
    
    return render(request, 'ParticipationFaculty_templates/create_participation_child.html',
                  {'val': val, 'participation': participation_parent, 'selected_options': selected_options})
                  



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
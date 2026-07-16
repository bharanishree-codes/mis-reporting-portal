from django.shortcuts import render, redirect, get_object_or_404
from MIS.functions import validate_file_format_faculty, validate_file_size
from django.http import HttpResponse
import requests, json
from django.contrib import messages
from datetime import datetime
from user_management.settings_views import user_bundle_settings
from user_management.settings_views import get_settings
from collections import Counter


API_STUDIO_URL = user_bundle_settings()



# Participation options list
PARTICIPATION_OPTIONS = ['Board of Studies', 'Question Paper Setting', 'Evaluation', 'Design and Development of Curriculum for ADD-On', 'Certificate Courses','External Examiner', 'Conference', 'Seminar', 'Workshop']
# Faculty authentication function to retrieve the access token
def faculty_auth():
    url = "https://api.hcaschennai.edu.in/auth/token"
    payload = json.dumps({"secret_key": "C4ZoXbsAnHLjk1Xyz4QPT2eoiNx6K6fo"})
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        response_data = response.json()
        access_token = response_data.get('access_token')
        token_type = response_data.get('token_type')
        return access_token, token_type
    else:
        return None, None
# Function to get employee data by stf_id

def faculty_token(access_token, token_type):
    url = "https://api.hcaschennai.edu.in/sqlviews/api/v1/auth/get_response_data"
    payload = json.dumps({"psk_uid": "51a531b4-bd55-491c-861d-a8d7227b325b","project": "hcas","data": {}})
    headers = {'Content-Type': 'application/json', 'Authorization': f'{token_type} {access_token}'}
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return None  # Return None on failure

def create_participation(request):
    access_token, token_type = faculty_auth()
    if not access_token or not token_type:
        error_message = 'Failed to get access token from API.'
        return render(request, 'ParticipationFaculty_templates/create_participation.html', {'error': error_message})
    # Fetch faculty data
    faculty_data = faculty_token(access_token, token_type)
    if not faculty_data:
        error_message = 'Failed to fetch staff data.'
        return render(request, 'ParticipationFaculty_templates/create_participation.html', {'error': error_message})
    current_year = datetime.now().year
    year = list(range(current_year + 1, 1999, -1))  # Descending order
    selected_year = 2025
    user = get_settings(request)
    username = user.get('username')
    # username = 'CS-T151'
    # username = 'AC-NT012'  # Predefined staff_id for the form
    print("staff_name", username)
    # Pre-filling staff name and department based on staff_id
    selected_faculty = None
    for faculty in faculty_data:
        if faculty['stf_id'] == username:
            selected_faculty = faculty
            break
    stf_name = selected_faculty.get('stf_name', '') if selected_faculty else ''
    department = selected_faculty.get('department', '') if selected_faculty else ''

    # For POST request (form submission)
    if request.method == 'POST':
        selected_options = request.POST.getlist('items')
        year = request.POST.get('year')
        name = request.POST.get('name')
        stf_id = username  # Getting the staff_id submitted via the form
        # Initialize the selected faculty as None
        selected_faculty = None
        # Loop through each faculty in the faculty_data to find the matching stf_id
        for faculty in faculty_data:
            if faculty['stf_id'] == stf_id:
                selected_faculty = faculty  # Assign the matching faculty
                break  # Stop the loop once the faculty is found
        # If a matching faculty was found, extract the data
        if selected_faculty:
            depcode = selected_faculty.get('depcode', '')
            department = selected_faculty.get('department', '')
            stf_name = selected_faculty.get('stf_name', '')
            # Prepare data to send to the external API
            url = f"{API_STUDIO_URL}postapi/create/naac01_faculty_participation_dc1"
            create_data = {"data": {"name": name, "year": year, "participation": ', '.join(selected_options), "stf_id": stf_id, "depcode": depcode, "department": department, "stf_name": stf_name}}
            create_payload = json.dumps(create_data)
            # Send data to the external API
            headers = {'Content-Type': 'application/json', 'Authorization': f'{token_type} {access_token}'}
            response = requests.post(url, headers=headers, data=create_payload)
            # Check API response
            if response.status_code == 200:
                psk_id = response.json().get('psk_id')
                return redirect('detail_view', id=psk_id)
            else:
                return HttpResponse("Failure: " + response.text)
        else:
            error_message = "Selected faculty not found."
            return render(request, 'ParticipationFaculty_templates/create_participation.html', {'error': error_message, 'options': PARTICIPATION_OPTIONS, 'faculty_data': faculty_data})
    # For GET request (initial load of the form)
    return render(request, 'ParticipationFaculty_templates/create_participation.html', {'options': PARTICIPATION_OPTIONS,'faculty_data': faculty_data,'year': year,'staff_id': username,'stf_name': stf_name,'department': department,})



def detail_view(request, id):
    # Fetch parent participation data
    parent_url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc1/{id}"
    parent_res = requests.get(parent_url)

    if parent_res.status_code != 200:
        return HttpResponse(f"Error fetching participation details: {parent_res.text}")

    participation = parent_res.json()
    
    parent_id = participation.get('psk_id')
    selected_options = participation.get('participation', '').split(', ')
    year = request.POST.get('year', participation.get('year', ''))

    # Fetch child participation records
    # query_payload = 
    payload = json.dumps({"queries": [{"field": "transaction_id", "value": parent_id, "operation": "equal"}],"search_type": "all"})
    child_res = requests.get(url=f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc2", headers={'Content-Type': 'application/json'}, data=payload)

    children = child_res.json() if child_res.status_code == 200 else []

    # Fetch media for each child
    for child in children:
        child_id = child.get('psk_id')
        media_url = f"{API_STUDIO_URL}crudapp/get/media/naac01_faculty_participation_dc2_media/parent/{child_id}"
        media_res = requests.get(media_url)
        child['media'] = [item.get('file_name') for item in media_res.json()] if media_res.status_code == 200 else []

    # Field map for validation
    field_map = {
        'board of studies': ['board_university_college_name', 'board_designation'],
        'question paper setting': ['qp_university_college_name', 'qp_subject'],
        'evaluation': ['eval_university_college_name', 'eval_subject'],
        'design and development of curriculum for add-on': ['design_development_university_college_name', 'design_development_addon'],
        'certificate courses': ['certificate_university_college_name', 'certificate_course'],
        'external examiner': ['external_examiner_university_college_name'],
        'conference': ['conference_university_college_name', 'conference_name'],
        'seminar': ['seminar_university_college_name', 'seminar_name'],
        'workshop': ['workshop_university_college_name', 'workshop_name']
    }

    # Validate on POST
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
            return render(request, "ParticipationFaculty_templates/detail_view.html", {'participation': participation,'selected_options': selected_options,'children': children,'year': year,'missing_children': missing_children})

        messages.success(request, "Participation data processed successfully!")
        return redirect('list_participations')

    # GET request
    return render(request, "ParticipationFaculty_templates/detail_view.html", {'participation': participation,'selected_options': selected_options,'children': children,'year': year,'missing_children': []})

# def list_participations(request):
    # url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc1/all"
    # response = requests.get(url)
    
    # if response.status_code == 200:
        # participations = response.json()
        # print("participations:", participations)
    # else:
        # return HttpResponse("API Call Is Not Working")

    # user = get_settings(request)
    # username = user.get('username')
    # # username = 'CS-T151'
    
    # # Filter participations by staff ID
    # filtered_participations = [participation for participation in participations if participation.get('stf_id') == username]
    
    # # Clean up: Remove parent records without children
    # participations_to_keep = []
    # for participation in filtered_participations:
        # parent_id = participation.get('psk_id')
        
        # # Check if this parent has any children
        # child_url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc2"
        # payload = json.dumps({
            # "queries": [{"field": "transaction_id", "value": parent_id, "operation": "equal"}],
            # "search_type": "all"
        # })
        # headers = {'Content-Type': 'application/json'}
        # children_response = requests.get(child_url, headers=headers, data=payload)
        
        # if children_response.status_code == 200:
            # children = children_response.json()
            # if children:  # If there are children, keep this parent
                # participations_to_keep.append(participation)
            # else:  # If no children, delete the parent
                # delete_url = f"{API_STUDIO_URL}deleteapi/delete/naac01_faculty_participation_dc1/{parent_id}"
                # delete_response = requests.request("DELETE", delete_url)
                # if delete_response.status_code == 200:
                    # print(f"Deleted parent record {parent_id} with no children")
                # else:
                    # print(f"Failed to delete parent record {parent_id}")
    
    # # Check if staff_id filter is applied from GET parameter
    # selected_staff_id = request.GET.get('staff_id')
    # from_dashboard = request.GET.get('from') == 'dashboard' or 'admin_hod_dash' or 'admin_dash' or 'department_dashboard'
    
    # if selected_staff_id:
        # # Re-filter if a specific staff_id is requested
        # participations_to_keep = [participation for participation in participations_to_keep if participation.get('stf_id') == selected_staff_id]
    
    # if not participations_to_keep:
        # return render(request, 'ParticipationFaculty_templates/list_participations.html', {"participations": []})
    
    # return render(request, 'ParticipationFaculty_templates/list_participations.html', {
        # "participations": participations_to_keep, 
        # 'from_dashboard': from_dashboard
    # })


# def list_participations(request):
#     url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc1/all"
#     response = requests.get(url)
    
#     if response.status_code == 200:
#         participations = response.json()
#         print("participations:", participations)
#     else:
#         return HttpResponse("API Call Is Not Working")

#     user = get_settings(request)
#     # username = user.get('username')
#     username = 'CS-T151'
#     filtered_participations = [participation for participation in participations if participation.get('stf_id') == username]
    
#     selected_staff_id = request.GET.get('staff_id')
#     from_dashboard = request.GET.get('from') == 'dashboard' or 'admin_hod_dash' or 'admin_dash' or 'department_dashboard'
    
#     if selected_staff_id:
#         filtered_participations = [participation for participation in participations if participation.get('stf_id') == selected_staff_id]
    
#     if not filtered_participations:
#         return render(request, 'ParticipationFaculty_templates/list_participations.html', {"participations": []})
    
#     return render(request, 'ParticipationFaculty_templates/list_participations.html', {"participations": filtered_participations, 'from_dashboard': from_dashboard})



def update_participation(request, id):
    url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc1/{id}"
    response = requests.get(url)
    participation = response.json()
    current_year = datetime.now().year
    year = list(range(current_year + 1, 1999, -1))  # Descending order
    selected_options = participation.get('participation', '').split(', ') if 'participation' in participation else []
    
    children_url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc2"
    payload = json.dumps({"queries": [{"field": "transaction_id", "value": id, "operation": "equal"}], "search_type": "all"})
    headers = {'Content-Type': 'application/json'}
    children_response = requests.get(children_url, headers=headers, data=payload)

    if children_response.status_code == 200:
        my_child = children_response.json()
    else:
        return HttpResponse(f"Error fetching children details: {children_response.text}", status=500)

    if request.method == "POST":
        selected_options_from_form = request.POST.getlist('items')
        
        # Step 5: Check if any selected option with children is being deselected
        options_with_children = []
        
        field_map = {
                'board of studies': ['board_university_college_name', 'board_designation'],
                'question paper setting': ['qp_university_college_name', 'qp_subject'],
                'evaluation': ['eval_university_college_name', 'eval_subject'],
                'Design and Development of Curriculum for ADD-On': ['design_development_university_college_name', 'design_development_addon'],
                'certificate courses': ['certificate_university_college_name', 'certificate_course'],
                'external examiner': ['external_examiner_university_college_name'],
                'conference': ['conference_university_college_name', 'conference_name'],
                'seminar': ['seminar_university_college_name', 'seminar_name'],
                'workshop': ['workshop_university_college_name', 'workshop_name']
            }

        # Check if each selected option has corresponding child data
        for option in selected_options:
            option_key = option.lower()
            has_children = False

            # Iterate over the children data to find if there's a child for the current option
            for child in my_child:
                # Check for each field in the field_map based on the option
                required_fields = field_map.get(option_key, [])
                if all(child.get(field) for field in required_fields):
                    has_children = True
                    break

            if has_children and option not in selected_options_from_form:
                options_with_children.append(option)

        # Step 6: If we find any deselected options with children, show an error
        if options_with_children:
            error_message = f"Cannot deselect the following options because they have associated children: {', '.join(options_with_children)}"
            messages.error(request, error_message)
            
            # Return the page with the previously selected options and the participation data
            return render(request, 'ParticipationFaculty_templates/update_participation.html', {'participation': participation,'selected_options': selected_options,'years': years,'options': PARTICIPATION_OPTIONS})
        
        # If no error, proceed with the update
        name = request.POST.get('name', participation.get('name', ''))
        year = request.POST.get('year', participation.get('year', ''))
        participation_type = ', '.join(request.POST.getlist('items'))
        selected_options = ', '.join(selected_options_from_form)  # Final list of selected options
        update_url = f"{API_STUDIO_URL}updateapi/update/naac01_faculty_participation_dc1/{id}"
        payload = json.dumps({"data": {"name": name, "year": year, "participation": participation_type}})
        headers = {'Content-Type': 'application/json'}
        update_response = requests.put(update_url, headers=headers, data=payload)

        if update_response.status_code == 200:
            return redirect('detail_view', id=participation.get('psk_id'))
        else:
            return HttpResponse("Failed to update participation: " + update_response.text)

    # GET request - render the page with the initial data
    return render(request, 'ParticipationFaculty_templates/update_participation.html', {'participation': participation,'selected_options': selected_options,'years': years,'options': PARTICIPATION_OPTIONS})

def delete_participation(request, id):
    
        delete_url = f"{API_STUDIO_URL}deleteapi/delete/naac01_faculty_participation_dc1/{id}"
        
        payload = ""
        headers = {}

        delete_response = requests.request("DELETE", delete_url, headers=headers, data=payload)

        if delete_response.status_code == 200:
            messages.success(request, message=f"The Article was deleted successfully.")
            return redirect('list_participations')
        else:
            # Error message in case of failure
            error_msg = delete_response.json()
            messages.error(request, message=f"{error_msg.get('detail', 'Failed to delete participation')}")

def list_all_participation_children(request):
    # Step 1: Get all participation records
    participation_api = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc1/all"
    response = requests.get(participation_api)
    if response.status_code != 200:
        return HttpResponse("Could not load participation data")
    participation_data = response.json()

    # Step 2: Determine final staff ID to filter
    user = get_settings(request)
    username = user.get('username')
    # username = 'CS-T151'
    final_staff_id = request.GET.get("staff_id") or username

    # Step 3: Filter participation by staff and category
    selected_category = request.GET.get("category")
    categories = ["Board of Studies", "Question Paper Setting", "Evaluation","Design and Development", "Certificate Courses", "External Examiner","Conference", "Seminar", "Workshop"]

    filtered_data = [participation for participation in participation_data if participation.get("stf_id") == final_staff_id and (not selected_category or selected_category in [category.strip() for category in participation.get("participation", "").split(",")])]

    # Step 4: Determine selected participation types
    selected_types = {selected_category} if selected_category in categories else {c.strip() for p in filtered_data for c in p.get("participation", "").split(",") if c.strip() in categories}

    # Step 5: Count participation types
    counts = Counter(t.strip().replace(" ", "_") for p in filtered_data for t in p.get("participation", "").split(",") if t.strip())

    # Step 6: Load child records
    child_api = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc2/all"
    child_response = requests.get(child_api)
    if child_response.status_code != 200:
        return HttpResponse("Could not load child records")
    child_data = child_response.json()

    # Step 7: Match child records with selected types and staff participation
    staff_psk_ids = {p.get("psk_id") for p in filtered_data}
    print("staff_psk_ids:", staff_psk_ids)
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
        }
        field = key_map.get(cat)
        matching_children = [child for child in child_data if child.get("transaction_id") in staff_psk_ids and child.get(field)]

        # Step 8: Add media files to children
        for child in matching_children:
            child["media"] = []
            psk_id = child.get("psk_id")
            if psk_id:
                media_url = f"{API_STUDIO_URL}crudapp/get/media/naac01_faculty_participation_dc2_media/parent/{psk_id}"
                media_response = requests.get(media_url)
                if media_response.status_code == 200:
                    child["media"] = [m.get("file_name") for m in media_response.json()]

        final_children.append((cat, matching_children))

    # Step 9: Render the results
    return render(request, "ParticipationFaculty_templates/list_participation_children.html", {"participation": filtered_data,"selected_options": selected_types,"children_by_option": final_children,"participation_counts": counts,"username": final_staff_id})

field_map = {
    'board of studies': ['board_university_college_name', 'board_designation'],
    'question paper setting': ['qp_university_college_name', 'qp_subject'],
    'evaluation': ['eval_university_college_name', 'eval_subject'],
    'design and development of curriculum for add-on': ['design_development_university_college_name', 'design_development_addon'],
    'certificate courses': ['certificate_university_college_name', 'certificate_course'],
    'external examiner': ['external_examiner_university_college_name'],
    'conference': ['conference_university_college_name', 'conference_name'],
    'seminar': ['seminar_university_college_name', 'seminar_name'],
    'workshop': ['workshop_university_college_name', 'workshop_name']
}

def clean_all_participations(request):
    parent_url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc1"
    parent_res = requests.get(parent_url)

    if parent_res.status_code != 200:
        messages.error(request, "Could not fetch participation records.")
        return redirect('dashboard')

    all_parents = parent_res.json()  # list of parent dicts

    for parent in all_parents:
        parent_id = parent.get("psk_id")
        if not parent_id:
            continue

        selected_options = [opt.strip().lower() for opt in parent.get("participation", "").split(",") if opt.strip()]
        if not selected_options:
            continue

        # Fetch child records
        child_payload = json.dumps({"queries": [{"field": "transaction_id", "value": parent_id, "operation": "equal"}],"search_type": "all"})
        child_url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc2"
        child_res = requests.get(child_url, headers={'Content-Type': 'application/json'}, data=child_payload)
        children = child_res.json() if child_res.status_code == 200 else []

        valid_children = []
        for child in children:
            for option in selected_options:
                required_fields = field_map.get(option, [])
                if all(child.get(f) for f in required_fields):
                    valid_children.append(child)
                    break
            else:
                del_url = f"{API_STUDIO_URL}crudapp/delete/naac01_faculty_participation_dc2/{child.get('psk_id')}"
                requests.delete(del_url)

        # Delete parent if no valid children remain
        if not valid_children:
            del_parent_url = f"{API_STUDIO_URL}crudapp/delete/naac01_faculty_participation_dc1/{parent_id}"
            requests.delete(del_parent_url)

    messages.success(request, "All participation records cleaned.")
    return redirect('dashboard')




def create_participation_child(request, participation_id, val):
    url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc1/{participation_id}"
    participation_parent_response = requests.get(url)
    if participation_parent_response.status_code == 200:
        participation_parent = participation_parent_response.json()
        transaction_id = participation_parent_response.json().get('psk_id')
        selected_options = participation_parent.get('participation', '').split(', ') if participation_parent.get(
            'participation') else []
    else:
        return HttpResponse("Error fetching participation details: " + participation_parent_response.text)
    if request.method == 'POST':

        child_url = f"{API_STUDIO_URL}postapi/create/naac01_faculty_participation_dc2"

        payload = {'board_university_college_name': request.POST.get('board_university'),'board_designation': request.POST.get('board_designation'),'qp_university_college_name': request.POST.get('qp_university'),'qp_subject': request.POST.get('qp_subject'),'eval_university_college_name': request.POST.get('eval_institute'),'eval_subject': request.POST.get('eval_role'),'certificate_university_college_name': request.POST.get('cert_institute'),'certificate_course': request.POST.get('cert_course_name'),'external_examiner_university_college_name': request.POST.get('external_institute'),'conference_university_college_name': request.POST.get('conf_name'),'conference_name': request.POST.get('conf_role'),'seminar_university_college_name': request.POST.get('seminar_title'),'seminar_name': request.POST.get('seminar_role'),'workshop_university_college_name': request.POST.get('workshop_title'),'workshop_name': request.POST.get('workshop_role'),'design_development_university_college_name': request.POST.get('curriculum_institute'),'design_development_addon': request.POST.get('curriculum_role'), 'transaction_id': transaction_id}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(child_url, headers=headers, data=json.dumps({"data": payload}))

        if response.status_code != 200:
            return HttpResponse("Failed to create participation child: " + response.text)

        child_data = response.json()
        child_id = child_data.get('psk_id')

        media_url = f"{API_STUDIO_URL}crudapp/upload/media/naac01_faculty_participation_dc2_media/"

        uploaded_file = request.FILES.get('file')
        validate_file_size(uploaded_file)
        validate_file_format_faculty(uploaded_file)

        file_type = uploaded_file.content_type

        payload = {'parent_psk_id': child_id}

        files = {'media': (uploaded_file.name, uploaded_file, file_type)}

        headers = {'api_name': 'naac01_faculty_participation_dc2_media'}

        media_response = requests.post(media_url, headers=headers, data=payload, files=files)

        if media_response.status_code == 200:

            return redirect('detail_view', id=participation_id)
        else:
            return HttpResponse("Failed to upload media files: " + media_response.text)
    return render(request, 'ParticipationFaculty_templates/create_participation_child.html',
                  {'val': val, 'participation': participation_parent, 'selected_options': selected_options})

def update_participation_child(request, participation_id, child_id, val):
    # Fetch participation parent data
    url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc1/{participation_id}"
    participation_parent_response = requests.get(url)
    
    response = participation_parent_response.json()
    id = response.get('psk_id')
    print(id)
    
    if participation_parent_response.status_code == 200:
        participation_parent = participation_parent_response.json()
        name = participation_parent.get('name')
        year = participation_parent.get('year')
        selected_options = participation_parent.get('participation', '').split(', ') if participation_parent.get('participation') else []
    else:
        return HttpResponse(f"Error fetching participation details: {participation_parent_response.text}")

    # Fetch child data
    child_url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc2/{child_id}"
    headers = {'Content-Type': 'application/json'}
    response = requests.get(child_url, headers=headers)

    if response.status_code == 200:
        child_data = response.json()
    else:
        return HttpResponse(f"Failed to fetch child data: {response.text}")

    # Fetch media details before POST request
    media_url = f"{API_STUDIO_URL}crudapp/get/media/naac01_faculty_participation_dc2_media/parent/{child_id}"
    media_response = requests.get(media_url, headers=headers)

    if media_response.status_code == 200:
        media_data = media_response.json()
        value_id = media_data[0]['psk_id'] if media_data else None
        file_name = media_data[0]['file_name'] if media_data else None
        print('media_data:', file_name)
    else:
        return HttpResponse(f"Failed to fetch media data: {media_response.text}")

    # Initialize file to None in case no file is uploaded

    if request.method == 'POST':
        # Update child data
        update_url = f"{API_STUDIO_URL}updateapi/update/naac01_faculty_participation_dc2/{child_id}"

        payload = json.dumps({"data": {"board_university_college_name": request.POST.get('board_university', ''),"board_designation": request.POST.get('board_designation', ''),"qp_university_college_name": request.POST.get('qp_university', ''),"qp_subject": request.POST.get('qp_subject', ''),"eval_university_college_name": request.POST.get('eval_institute', ''),"eval_subject": request.POST.get('eval_role', ''),"certificate_university_college_name": request.POST.get('cert_institute', ''),"certificate_course": request.POST.get('cert_course_name', ''),"external_examiner_university_college_name": request.POST.get('external_institute', ''),"conference_university_college_name": request.POST.get('conf_name', ''),"conference_name": request.POST.get('conf_role', ''),"seminar_university_college_name": request.POST.get('seminar_title', ''),"seminar_name": request.POST.get('seminar_role', ''),"workshop_university_college_name": request.POST.get('workshop_title', ''),"workshop_name": request.POST.get('workshop_role', ''),"design_development_university_college_name": request.POST.get('curriculum_institute', ''),"design_development_addon": request.POST.get('curriculum_role', '')}})
        headers = {'Content-Type': 'application/json'}
        update_response = requests.put(update_url, headers=headers, data=payload)

        if update_response.status_code != 200:
            return HttpResponse(f"Failed to update participation child: {update_response.text}")

        # If no file uploaded, continue with the current media and redirect
        uploaded_file = request.FILES.get('file')

        if uploaded_file:
            validate_file_size(uploaded_file)
            validate_file_format_faculty(uploaded_file)
            # If a file is uploaded, handle file update
            if value_id:  # Check if media exists
                url = f"{API_STUDIO_URL}crudapp/upload/media/naac01_faculty_participation_dc2_media/{value_id}"
                
                file_type = uploaded_file.content_type
                payload = {'parent_psk_id': child_id}
                files = {'media': (uploaded_file.name, uploaded_file, file_type)}
                headers = {'api_name': 'naac01_faculty_participation_dc2_media', 'psk_id': str(value_id)}

                upload_response = requests.put(url, headers=headers, data=payload, files=files)

                if upload_response.status_code != 200:
                    return HttpResponse(f"Failed to upload media files: {upload_response.text}")

        # Redirect to the detail view after successful update (with or without file update)
        return redirect('detail_view', id=participation_id)

    # Render the template with existing data
    return render(request, 'ParticipationFaculty_templates/update_participation_child.html', {'val': val, 'participation': participation_id, 'child': child_data, 'name': name, 'year': year, 'selected_options': selected_options, 'value_id': value_id, 'id': id, 'file_name':file_name})

def delete_participation_child(request, child_id, participation_id):
    # Handle only POST requests for deletion
    # if request.method == 'POST':
        delete_url = f"{API_STUDIO_URL}deleteapi/delete/naac01_faculty_participation_dc2/{child_id}"

        payload = ""
        headers = {}

        # Sending DELETE request
        delete_response = requests.request("DELETE", delete_url, headers=headers, data=payload)

        # If the deletion is successful, show success message and redirect
        if delete_response.status_code == 200:
            messages.success(request, "The child participation was deleted successfully.")
            return redirect('detail_view', id=participation_id)
        else:
            # If deletion failed, show error message with details
            error_msg = delete_response.json() if delete_response.status_code == 400 else {}
            messages.error(request, f"Failed to delete child participation: {error_msg.get('detail', 'Unknown error')}")




# def list_options_participations(request):
    # url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc1/all"
    # response = requests.get(url)
    
    # if response.status_code != 200:
        # return HttpResponse("API Call Is Not Working")

    # participations = response.json()
    # print(participation)
   
    # # Count how many times each participation option is used
    # option_counter = Counter()
    # for participation in participations:
        # # print("participations:", participations)
        # options = participation.get('participation', '')
        # if options:
            # option_list = [opt.strip() for opt in options.split(',')]
            # option_counter.update(option_list)

    # # Ensure all options are present with a default of 0
    # participation_option_counts = {option: option_counter.get(option, 0) for option in PARTICIPATION_OPTIONS}

    # return render(request, 'ParticipationFaculty_templates/list_options_participations.html', {'participations': participations,'participation_option_counts': participation_option_counts})
    
    
    
def cleanup_orphan_participations():
    """Function to delete all parent records without children"""
    parent_url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc1/all"
    parent_res = requests.get(parent_url)
    
    if parent_res.status_code != 200:
        return
    
    all_parents = parent_res.json()
    
    for parent in all_parents:
        parent_id = parent.get("psk_id")
        if not parent_id:
            continue
        
        # Check for children
        child_url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc2"
        payload = json.dumps({
            "queries": [{"field": "transaction_id", "value": parent_id, "operation": "equal"}],
            "search_type": "all"
        })
        headers = {'Content-Type': 'application/json'}
        children_response = requests.get(child_url, headers=headers, data=payload)
        
        children = children_response.json() if children_response.status_code == 200 else []
        
        if not children:  # No children found, delete parent
            delete_url = f"{API_STUDIO_URL}deleteapi/delete/naac01_faculty_participation_dc1/{parent_id}"
            requests.delete(delete_url)
            print(f"Deleted orphan parent record: {parent_id}")
 


def list_participations(request):

    cleanup_orphan_participations()

    url = f"{API_STUDIO_URL}getapi/all_fields/naac01_faculty_participation_dc1/all"
    response = requests.get(url)
    
    if response.status_code == 200:
        participations = response.json()
    else:
        return HttpResponse("API Call Is Not Working")

    user = get_settings(request)
    username = user.get('username')
    # username = 'AD-NT020'

    # Staff ID filter (from GET param or fallback to logged-in user)
    selected_staff_id = request.GET.get('staff_id')
    staff_id_to_use = selected_staff_id if selected_staff_id else username

    # Filter participations for the chosen staff
    filtered_participations = [
        p for p in participations if p.get('stf_id') == staff_id_to_use
    ]

    # Clean up: Keep only participations that have children
    participations_to_keep = []
    for participation in filtered_participations:
        parent_id = participation.get('psk_id')
        
        child_url = f"{API_STUDIO_URL}getapi/naac01_faculty_participation_dc2"
        payload = json.dumps({
            "queries": [{"field": "transaction_id", "value": parent_id, "operation": "equal"}],
            "search_type": "all"
        })
        headers = {'Content-Type': 'application/json'}
        children_response = requests.get(child_url, headers=headers, data=payload)

        if children_response.status_code == 200:
            children = children_response.json()
            if children:  # If children exist → keep parent
                participations_to_keep.append(participation)
            else:  # No children → delete parent record
                delete_url = f"{API_STUDIO_URL}deleteapi/delete/naac01_faculty_participation_dc1/{parent_id}"
                delete_response = requests.delete(delete_url)
                if delete_response.status_code == 200:
                    print(f"Deleted parent record {parent_id} with no children")

    # Final participation count
    participation_count = len(participations_to_keep)

    # Pass both participations + count to template
    return render(request, 'ParticipationFaculty_templates/list_participations.html', {
        "participations": participations_to_keep,
        "participation_count": participation_count,
        "selected_staff_id": staff_id_to_use
    })
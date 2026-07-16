import aiohttp
import re
import asyncio
import json

FASTAPI_BASE_URL = "https://fastapi.hcaschennai.edu.in"

# Authentication config
AUTH_CONFIG = {
    "user_type": "student",
    "secret_password": "b2e_meritplus_2025",
    "user_url": "http://fastapi.hcaschennai.edu.in/",
    "user_key": "ADMN20221785"
}

class FastAPIAuth:
    def __init__(self):
        self.access_token = None

    async def get_access_token(self):
        """Authenticate and return JWT token (no try/except used)."""

        # Return cached token
        if self.access_token:
            return self.access_token

        # Step 1: Get Secret Key
        secret_key_url = f"{FASTAPI_BASE_URL}/erp/v1/rbac/generate/secretkey"
        secret_key_payload = {
            "user_key": AUTH_CONFIG["user_key"],
            "user_type": AUTH_CONFIG["user_type"],
            "secrete_key": AUTH_CONFIG["secret_password"],
            "user_url": AUTH_CONFIG["user_url"]
        }

        async with aiohttp.ClientSession() as session:

            secret_response = await session.post(
                secret_key_url,
                json=secret_key_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if secret_response.status != 200:
                return None

            secret_data = await secret_response.json()
            secret_key = secret_data.get("secret_key")

            if not secret_key:
                return None

            # Step 2: Generate access token
            token_url = f"{FASTAPI_BASE_URL}/erp/v1/rbac/generate/token"
            token_payload = {"secret_key": secret_key}

            token_response = await session.post(
                token_url,
                json=token_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if token_response.status != 200:
                return None

            token_data = await token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                return None

            self.access_token = access_token
            return self.access_token


# Global instance
auth_client = FastAPIAuth()


async def call_fastapi_endpoint(endpoint: str, method: str = "GET", data: dict = None):
    """Call any FastAPI endpoint using JWT token (no try/except used)."""

    token = await auth_client.get_access_token()

    if not token:
        return {"error": "Authentication failed. Could not get access token."}

    url = f"{FASTAPI_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:

        # GET Method
        if method.upper() == "GET":
            response = await session.get(url, headers=headers, timeout=10)
            text = await response.text()
            return json.loads(text) if text.startswith("{") else text

        # POST Method
        if method.upper() == "POST":
            response = await session.post(url, json=data, headers=headers, timeout=10)
            text = await response.text()
            return json.loads(text) if text.startswith("{") else text

        # Other methods can be added
        return {"error": "Unsupported HTTP method."}


async def get_ai_tool_response(prompt: str) -> str:
    """Parse prompt and route to correct API."""
    print(f"Processing prompt: {prompt}")

    student_id = extract_student_id(prompt)

    if student_id:
        data = await call_fastapi_endpoint(f"/erp/v1/student/personal_info/{student_id}")

        if isinstance(data, dict) and "error" in data:
            return f"Error: {data['error']}"

        return format_raw_response(data, f"Student Details for ID: {student_id}")

    return "Please provide a student ID. Example: 'Get student details for ID 21654'"


def extract_student_id(prompt: str) -> int:
    """Extract student ID using multiple regex patterns."""

    patterns = [
        r'stu_KEY\s*(\d+)',
        r'student\s*ID\s*(\d+)',
        r'ID\s*(\d+)',
        r'student.*?(\d+)',
        r'(\d{4,})'
    ]

    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            num = match.group(1)
            return int(num) if num.isdigit() else None

    return None


# def format_raw_response(data: dict, title: str = "API Response") -> str:
#     """Format dictionary response into readable text."""

#     if not isinstance(data, dict):
#         return str(data)

#     response = [f"{title}:\n"]
#     for key, value in data.items():
#         response.append(f"{key}: {value}")

#     return "\n".join(response)



def format_raw_response(data: dict, title: str = "API Response") -> str:
    """Convert raw DB fields into well-structured student information."""

    if not isinstance(data, dict):
        return str(data)

    # Safe getter
    def val(key):
        return data.get(key, "")

    response = [
        f"Here are the complete details for student {val('stu_name')}:\n"
    ]

    # ---------------------------------------------------------
    # PERSONAL INFORMATION
    # ---------------------------------------------------------
    response.append("🔹 PERSONAL INFORMATION:\n")
    response.append(f"Student ID: {val('stu_ID')}")
    response.append(f"Name: {val('stu_salutation')} {val('stu_name')} {val('stu_mname')} {val('stu_lname')}")
    response.append(f"Roll Number: {val('stu_rollno')}")
    response.append(f"Temporary Roll No: {val('stu_temprollno')}")
    response.append(f"DOB: {val('stu_DOB')}")
    response.append(f"DOB SMS: {val('stu_dobsms')}")
    response.append(f"Birthplace: {val('stu_birthplace')}")
    response.append(f"Gender: {val('stu_GENDER')}")
    response.append(f"Blood Group: {val('stu_bloodgroup')}")
    response.append(f"Height: {val('stu_HEIGHT')}")
    response.append(f"Weight: {val('stu_WEIGHT')}")
    response.append(f"Nationality: {val('stu_nationality')} (lookup)")
    response.append(f"Religion: {val('stu_religion')} (lookup)")
    response.append(f"Caste: {val('stu_caste')}")
    response.append(f"Sub Caste: {val('stu_subcaste')}")
    response.append(f"Mother Tongue: {val('stu_mothertounge')} (lookup)")
    response.append(f"Special Category: {val('stu_specialcatagory')} (lookup)")
    response.append(f"Orphan Category: {val('stu_orphancategory')}")
    response.append(f"UDID No: {val('stu_udidno')}")
    response.append(f"UDID Reason: {val('stu_udidreasonid')}")
    response.append(f"Aadhar No: {val('aadharno')}")
    response.append(f"Aadhar Seeding Status: {val('stu_aadharseedingstatus')}")
    response.append(f"Aadhar Remark: {val('stu_aadharremarkmessage')}")
    response.append(f"PAN No: {val('panno')}")
    response.append(f"Others: {val('stu_others')}")
    response.append(f"Remarks: {val('remarks')}")
    response.append(f"Encrypted URL: {val('stu_encry_url')}")
    response.append("")

    # ---------------------------------------------------------
    # ACADEMIC INFORMATION
    # ---------------------------------------------------------
    response.append("🔹 ACADEMIC INFORMATION:\n")
    response.append(f"Class: {val('stu_Class')}")
    response.append(f"Class ID: {val('stu_classid')}")
    response.append(f"Section: {val('stu_section')}")
    response.append(f"Program ID: {val('stu_programid')}")
    response.append(f"Branch ID: {val('stu_branchid')}")
    response.append(f"Course ID: {val('stu_courseid')}")
    response.append(f"Year: {val('stu_year')}")
    response.append(f"Admission No: {val('stu_admissionno')}")
    response.append(f"Academic Year: {val('stu_acdyear')}")
    response.append(f"Academic Year (New): {val('stu_acadamicyear')}")
    response.append(f"Admission Date: {val('stu_admissiondt')}")
    response.append(f"Admitted On: {val('stu_admiton')}")
    response.append(f"Admission Type: {val('stu_admissiontype')}")
    response.append(f"Admission Quota: {val('stu_admissionquota')}")
    response.append(f"Admission Location: {val('stu_registerlocation')}")
    response.append(f"Admission Reference: {val('stu_reference')}")
    response.append(f"Referred By: {val('stu_referralname')}")
    response.append(f"Source: {val('stu_source')}")
    response.append(f"Language Opted: {val('languageopted')}")
    response.append(f"Concession %: {val('stu_consper')}")
    response.append(f"10th %: {val('stu_xper')}")
    response.append(f"12th %: {val('stu_xiiper')}")
    response.append("")

    # ---------------------------------------------------------
    # ADDRESS INFORMATION
    # ---------------------------------------------------------
    response.append("🔹 ADDRESS INFORMATION:\n")
    response.append(f"Address: {val('stu_address1')} {val('stu_address2')} {val('stu_address3')} {val('stu_address4')}")
    response.append(f"State: {val('stu_state')}")
    response.append(f"District: {val('stu_district')}")
    response.append(f"Zip Code: {val('stu_zipcode')}")
    response.append(f"Postal Address: {val('stu_postaladdress')}")
    response.append(f"Country: {val('stu_country')}")

    # Permanent Address
    response.append(f"Permanent Taluk: {val('stu_pertaluk')}")
    response.append(f"Permanent Village: {val('stu_pervillage')}")
    response.append(f"Permanent Block: {val('stu_perblock')}")
    response.append(f"Permanent Village Panchayat: {val('stu_pervillagepanchayat')}")

    # Communication Address
    response.append(f"Communication Taluk: {val('stu_comtaluk')}")
    response.append(f"Communication Village: {val('stu_comvillage')}")
    response.append(f"Communication Block: {val('stu_comblock')}")
    response.append(f"Communication Village Panchayat: {val('stu_comvillagepanchayat')}")
    response.append(f"Communication Country: {val('stu_comcountry')}")
    response.append(f"Communication State: {val('stu_comstate')}")
    response.append(f"Communication District: {val('stu_comdistrict')}")
    response.append(f"Communication Postal Address: {val('stu_compostaladdress')}")
    response.append(f"Communication Zip Code: {val('stu_comzipcode')}")
    response.append(f"Location Type: {val('stu_locationtype')}")
    response.append(f"Communication Location Type: {val('stu_comlocationtype')}")
    response.append("")

    # ---------------------------------------------------------
    # CONTACT DETAILS
    # ---------------------------------------------------------
    response.append("🔹 CONTACT DETAILS:\n")
    response.append(f"Mobile: {val('stu_mobile')}")
    response.append(f"Email: {val('stu_email')}")
    response.append(f"Parent Name: {val('stu_parentname')}")
    response.append(f"Parent Mobile: {val('stu_parentmobile')}")
    response.append(f"Parent Email: {val('stu_parentemail')}")
    response.append(f"Boarding House: {val('stu_House')}")
    response.append("")

    # ---------------------------------------------------------
    # TRANSPORT & HOSTEL
    # ---------------------------------------------------------
    response.append("🔹 TRANSPORT & HOSTEL:\n")
    response.append(f"Boarding Point: {val('stu_Boarding_Point')}")
    response.append(f"Bus No: {val('stu_Bus_No')}")
    response.append(f"Bus Flag: {val('stu_busflg')}")
    response.append(f"Hostel Flag: {val('stu_hosflg')}")
    response.append(f"Hostel ID: {val('stu_hostelid')}")
    response.append(f"Mess Flag: {val('stu_messflg')}")
    response.append("")

    # ---------------------------------------------------------
    # BANK DETAILS
    # ---------------------------------------------------------
    response.append("🔹 BANK DETAILS:\n")
    response.append(f"Bank ID: {val('bankid')}")
    response.append(f"Bank Name: {val('stu_bankname')}")
    response.append(f"Bank A/C No: {val('bankaccno')}")
    response.append(f"A/C Holder Name: {val('stu_bankaccholname')}")
    response.append(f"A/C Type: {val('stu_bankacctype')}")
    response.append(f"IFSC Code: {val('ifsc_code')}")
    response.append(f"Bank Branch: {val('stu_bankbranch')}")
    response.append(f"Bank City: {val('stu_bankcity')}")
    response.append("")

    # ---------------------------------------------------------
    # SYSTEM INFORMATION
    # ---------------------------------------------------------
    response.append("🔹 SYSTEM INFORMATION:\n")
    response.append(f"Profile Image Path: {val('stuprofileimgpath')}")
    response.append(f"Profile Image Name: {val('stuprofileimgname')}")
    response.append(f"RFID Card No: {val('rfidcardno')}")
    response.append(f"FP Enrollment No: {val('fpenrollno')}")
    response.append(f"FP Hostel Enrollment No: {val('fphostelenrollno')}")
    response.append(f"UHID Card No: {val('uhfidcardno')}")
    response.append(f"Device ID: {val('deviceid')}")
    response.append(f"FCM Token: {val('fcmtoken')}")
    response.append(f"Login Status: {val('loginstatus')}")
    response.append(f"Last Login: {val('lastlogin')}")
    response.append("")

    # ---------------------------------------------------------
    # WORKFLOW, STATUS, PROCESS
    # ---------------------------------------------------------
    response.append("🔹 STATUS, WORKFLOW & PROCESS:\n")
    response.append(f"Status Flag: {val('statusflag')}")
    response.append(f"WF Status: {val('wfstatus')}")
    response.append(f"Process ID: {val('processid')}")
    response.append(f"Status: {val('status')}")
    response.append(f"Revision: {val('revision')}")
    response.append(f"Status Date: {val('stu_statusdate')}")
    response.append(f"Status Remarks: {val('stu_statusremarks')}")
    response.append(f"Long Absence: {val('stu_longabs')}")
    response.append(f"Long Absence Reason: {val('stu_longabsreason')}")
    response.append(f"Bulk Update: {val('stu_bulkupdate')}")
    response.append(f"EMIS ID No: {val('stu_emisidno')}")
    response.append(f"UMIS ID No: {val('stu_umisidno')}")
    response.append(f"EMIS Reason ID: {val('stu_emisreasonid')}")
    response.append(f"SPL Category Reason ID: {val('stu_splcatgreasonid')}")
    response.append("")

    # ---------------------------------------------------------
    # MISCELLANEOUS
    # ---------------------------------------------------------
    response.append("🔹 MISC:\n")
    response.append(f"Excel Filename: {val('stu_excelfilename')}")
    response.append(f"Created On: {val('createdon')}")
    response.append(f"Created By: {val('createdby')}")
    response.append(f"Last Modified By: {val('lastmodifyby')}")
    response.append(f"Last Modified On: {val('lastmodifyon')}")
    response.append(f"Impact Reference ID: {val('imprefid')}")
    response.append(f"Franchise ID: {val('franchiseid')}")
    response.append("")

    return "\n".join(response)
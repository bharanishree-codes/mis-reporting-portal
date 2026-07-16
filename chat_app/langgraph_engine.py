from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Optional
import re
import requests
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Now fetch the keys from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SECRET_KEY_URL = os.getenv("SECRET_KEY_URL")
TOKEN_URL = os.getenv("TOKEN_URL")
STUDENT_API_URL = os.getenv("STUDENT_API_URL")
USER_TYPE = os.getenv("USER_TYPE")
USER_URL = os.getenv("USER_URL")
SECRET_PASSWORD = os.getenv("SECRET_PASSWORD")
FASTAPI_URL = os.getenv("FASTAPI_URL")


# ---------------- LLM ----------------
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7
)

# ---------------- State ----------------
class ChatState(TypedDict):
    user_query: str
    admission_id: Optional[str]
    student_info: Optional[dict]
    fees_info: Optional[dict]
    answer: Optional[str]
    polite_reply: Optional[str]


# ---------------- Helper Functions ----------------
def extract_admission_id(query):
    match = re.search(r"ADMN\d{8}", query.upper())
    return match.group(0) if match else None

def safe_json(response):
    """Safely parse JSON, return None if invalid"""
    try:
        return response.json()
    except json.JSONDecodeError:
        #print("---- JSON ERROR ----")
        #print("URL:", response.url)
        #print("Status:", response.status_code)
        #print("Raw Response:", response.text[:500])
        #print("--------------------")
        return None


def get_secret_key(user_key):
    payload = {
        "user_key": user_key,
        "secrete_key": SECRET_PASSWORD,
        "user_type": USER_TYPE,
        "user_url": USER_URL
    }
    
    response = requests.post(SECRET_KEY_URL, json=payload)
    data = safe_json(response)

    if not data:
        return None
    
    return data.get("secret_key")


def get_access_token(secret_key):
    payload = {"secret_key": secret_key}
    response = requests.post(TOKEN_URL, json=payload)

    data = safe_json(response)
    if not data:
        return None, None

    return data.get("access_token"), data.get("token_type")


def fetch_student_info(admission_id):
    secret_key = get_secret_key(admission_id)
    if not secret_key:
        #print("❌ Secret key not received")
        return None

    token, token_type = get_access_token(secret_key)
    if not token:
        #print("❌ Access token not received")
        return None

    headers = {"Authorization": f"{token_type} {token}"}
    response = requests.get(STUDENT_API_URL.format(admission_id), headers=headers)

    data = safe_json(response)
    if not data:
        #print("❌ Student API returned invalid JSON")
        return None

    return data


def fetch_fees_info(admission_id):
    # 1. Get secret key
    secret_key = get_secret_key(admission_id)
    if not secret_key:
        #print("❌ Secret key not received")
        return None

    # 2. Get access token
    token, token_type = get_access_token(secret_key)
    if not token:
        #print("❌ Access token not received")
        return None

    # 3. Build correct URL
    url = f"{FASTAPI_URL}erp/v1/student/mcp/payment/{admission_id}"

    # 4. Correct headers with token
    headers = {
        "Authorization": f"{token_type} {token}",
        "Content-Type": "application/json"
    }

    # 5. Make GET request properly
    response = requests.get(url, headers=headers)

    # 6. Parse JSON safely
    fees_data = safe_json(response)
    if not fees_data:
        #print("❌ Fees API returned invalid JSON or empty response")
        #print("Raw response:", response.text)
        return None
    
    return fees_data




# ---------------- Nodes ----------------
def node_extract_id(state: ChatState):
    state["admission_id"] = extract_admission_id(state["user_query"])
    return state


def node_student_api(state: ChatState):
    if state["admission_id"]:
        state["student_info"] = fetch_student_info(state["admission_id"])
    return state

def node_fees_api(state: ChatState):
    if state["admission_id"]:
        state["fees_info"] = fetch_fees_info(state["admission_id"])
    return state

def node_generate_polite_reply(state: ChatState):
    response = llm.invoke(f"Reply politely: {state['user_query']}")
    state["polite_reply"] = response.content
    return state




def node_llm_student(state: ChatState):
    prompt = ChatPromptTemplate.from_template("""
    You are an ERP AI assistant.

    User Query: {user_query}

    Student Info:
    {student_info}
                        `                         
    Fees Info:
    {fees_info}                                          

    Provide a clear and helpful response.
    """)

    chain = prompt | llm | StrOutputParser()

    state["answer"] = chain.invoke({
        "user_query": state["user_query"],
        "student_info": state["student_info"],
        "fees_info": state["fees_info"],
    })
    return state


def node_llm_general(state: ChatState):
    prompt = ChatPromptTemplate.from_template("""
    You are an ERP AI assistant.
    User asked: {user_query}
    
    Provide a general helpful answer.
    """)

    chain = prompt | llm | StrOutputParser()
    state["answer"] = chain.invoke({"user_query": state["user_query"]})
    return state


def route(state: ChatState):
    return "student" if state["admission_id"] else "general"


# ---------------- Build Graph ----------------
workflow = StateGraph(ChatState)

workflow.add_node("extract_id", node_extract_id)
workflow.add_node("student_api", node_student_api)
workflow.add_node("fees_api", node_fees_api)
workflow.add_node("student_llm", node_llm_student)
workflow.add_node("general_llm", node_llm_general)
workflow.add_node("polite_reply_node", node_generate_polite_reply)



workflow.set_entry_point("extract_id")

workflow.add_conditional_edges(
    "extract_id",
    route,
    {
        "student": "student_api",
        "general": "general_llm"
    }
)

workflow.add_edge("student_api", "fees_api")
workflow.add_edge("fees_api", "student_llm")
workflow.add_edge("student_llm", END)

# General queries without admission_id
workflow.add_edge("general_llm", END)

workflow.add_edge("general_llm", "polite_reply_node")
workflow.add_edge("polite_reply_node", END)


graph = workflow.compile()

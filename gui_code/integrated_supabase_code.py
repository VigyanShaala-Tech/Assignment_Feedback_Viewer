import streamlit as st
import pandas as pd
import re
from PIL import Image
from supabase import create_client, Client
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

SUPABASE_URL = st.secrets['supabase']['supabase_url']
SUPABASE_KEY = st.secrets['supabase']['supabase_key']

SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open("Student_Activity_Log").worksheet("Logs")

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

@st.cache_data(ttl=300)
def load_data_from_supabase():
    try:
        response = supabase.table('Student_Assignment_Status').select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error loading data from Supabase: {str(e)}")
        return pd.DataFrame()

st.markdown("""
    <style>
    .status-box {
        padding: 0.75rem 1rem;
        border-radius: 8px;
        font-weight: bold;
        display: inline-block;
        margin-top: 0.5rem;
        border: 1px solid transparent;
    }

    .status-red {
        background-color: #660000;
        border-color: #cc0000;
        color: #ffcccc;
    }
    .status-green {
        background-color: #003300;
        border-color: #00cc66;
        color: #ccffcc;
    }
    .status-orange {
        background-color: #663300;
        border-color: #ffaa00;
        color: #ffdd99;
    }
    .status-pink {
        background-color: #4d0033;
        border-color: #ff66cc;
        color: #ffcce6;
    }
    </style>
""", unsafe_allow_html=True)

co1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.image("gui_code/log.png", width=450)

df = load_data_from_supabase()

if df.empty:
    st.error("No data could be loaded from Supabase. Please check your connection.")
    st.stop()

list_of_assignments = {
    "Goal Setting": {
        "status": "assignment_goal_setting",
        "comment": "comments_assignment_goal_setting"
    },
    "LinkedIn Profile": {
        "status": "assignment_linkedin_profile",
        "comment": "comments_assignment_linkedin_profile"
    },
    "STEM Curiosity": {
        "status": "assignment_stem_curiosity",
        "comment": "comments_assignment_stem_curiosity"
    },
    "Career Journal": {
        "status": "assignment_career_journal",
        "comment": "comments_assignment_career_journal"
    }
}

def get_status(remark):
    if remark.strip().lower() == 'not submitted':
        return "Not Submitted", "red"
    elif remark.strip().lower() == 'accepted':
        return "Accepted", "green"
    elif remark.strip().lower() == 'rejected':
        return "Rejected", "orange"

def clean_line_end(line):
    if isinstance(line, str):
        cleaned = re.sub(r'[^\x00-\x7F]+', '', line)
        cleaned = re.sub(r'_x[0-9A-Fa-f]{4}_', '', cleaned)
        cleaned = re.sub(r'[^a-zA-Z0-9\s.#]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    return line

def parse_feedback(comment):
    if pd.isna(comment) or not comment:
        return "", ""
    cleaned_comment = clean_line_end(comment)
    hash_count = cleaned_comment.count('#')
    parts = cleaned_comment.split('#')
    parts = [part.strip() for part in parts if part.strip()]
    num_parts = len(parts)
    if num_parts == 0:
        return "", ""
    elif hash_count == 1:
        return "", cleaned_comment
    else:
        history = ' # '.join(parts[:-1])
        current = parts[-1]
        return history, current

st.title(" Assignment Feedback Viewer")
college_list = df['college_name'].dropna().unique()
selected_college = st.selectbox("College Names", sorted(college_list))

students = df[df['college_name'] == selected_college]['student_name'].dropna().unique()
selected_student = st.selectbox("Student Names", sorted(students))

assignment_list = list(list_of_assignments.keys())
selected_assignment = st.selectbox("Assignment Names", assignment_list)
status_col = list_of_assignments[selected_assignment]["status"]
comment_col = list_of_assignments[selected_assignment]["comment"]

student_row = df[(df['college_name'] == selected_college) &
                 (df['student_name'] == selected_student)]

if student_row.empty:
    st.warning("No data found for the selected combination.")
else:
    assignment_status = student_row.iloc[0][status_col]
    comment = student_row.iloc[0][comment_col]
    status_text, status_color = get_status(assignment_status)
    feedback_history, current_feedback = parse_feedback(comment)

    st.markdown(f"### Assignment: {selected_assignment}")
    st.markdown(f"<div class='status-box status-{status_color}'>Status: {status_text}</div>", unsafe_allow_html=True)
    st.markdown("### Current Feedback:")
    if not current_feedback:
        st.info("No feedback provided yet.")
    else:
        for line in current_feedback.split('\n'):
            if line.strip():
                st.text(f"- {line.strip()}.")

    st.markdown("### Feedback History:")
    if not feedback_history:
        st.info("No feedback history available.")
    else:
        parts = feedback_history.split('#')
        for idx, part in enumerate(parts, start=1):
            if part.strip():
                st.text(f"- Feedback{idx}: {part.strip()}.")
    
    timestamp = datetime.now(str(pytz.timezone('Asia/Kolkata'))
    log_row = [timestamp, selected_college, selected_student, selected_assignment, status_text, "Viewed"]

    try:
        sheet.append_row(log_row)
    except Exception as e:
        st.error(f"Could not log activity: {str(e)}")

    feedback_str = f"Student: {selected_student}\nCollege: {selected_college}\nAssignment: {selected_assignment}\nStatus: {status_text}\n\n"    
    feedback_str += f"Current Feedback:\n{current_feedback if current_feedback else 'No feedback provided.'}\n\n"
    feedback_str += f"Feedback History:\n{feedback_history if feedback_history else 'No feedback history available.'}"
    
    st.download_button("Download Complete Feedback", feedback_str, file_name=f"{selected_student}_{selected_assignment}_feedback.txt")

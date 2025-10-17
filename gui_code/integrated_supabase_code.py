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

def fetch_all_rows():
    all_rows = []
    page_size = 1000
    for i in range(0, 10000, page_size):  # up to 10,000 rows
        response = supabase.table('Student_Assignment_Status').select("*").range(i, i + page_size - 1).execute()
        data = response.data
        if not data:
            break
        all_rows.extend(data)
        if len(data) < page_size:
            break
    return pd.DataFrame(all_rows)

@st.cache_data(ttl=300)
def load_data_from_supabase():
    try:
        return fetch_all_rows()
    except Exception as e:
        st.error(f"Error loading data from Supabase: {str(e)}")
        return pd.DataFrame()


st.markdown("""
    <style>
    .status-box {
        padding: 0.75rem 1rem;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1.2rem;
        display: inline-block;
        margin-top: 0.5rem;
        border: 1px solid transparent;
    }

    .status-red {
        background-color: #660000;
        border-color: #cc0000;
        color: #ffcccc;
            font-size: 1.5rem;
    }
    .status-green {
        background-color: #69AB4A;
        border-color: #00cc66;
        color: #000000;
        font-size: 1.5rem;
    }
    .status-orange {
        background-color: #F79630;
        border-color: #ffaa00;
        color: #000000;
        font-size: 1.5rem;
    }
    .status-pink {
        background-color: #FFCC29;
        border-color: #ffccce6;
        color: #000000;
        font-size: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

co1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.image("gui_code/log.png", width=350)

df = load_data_from_supabase()

if df.empty:
    st.error("No data could be loaded from Supabase. Please check your connection.")
    st.stop()

list_of_assignments = {
    "SWOT": {
        "status": "assignment_swot",
        "comment": "comments_assignment_swot"
    },    
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
    },
    "Career Map": {
        "status": "assignment_career_map",
        "comment": "comments_assignment_career_map"
    },
    "Skill Gap Finder": {
        "status": "assignment_skill_gap_finder",
        "comment": "comments_assignment_skill_gap_finder"
    },
    "Career_Vision_Board": {
        "status": "assignment_career_vision_board",
        "comment": "comments_assignment_career_vision_board"
    },
    "CV_Resume": {
        "status": "assignment_cv_resume",
        "comment": "comments_assignment_cv_resume"
    }
}

def get_status(remark):
    if remark.strip().lower() == 'not submitted':
        return "Not Submitted", "red"
    elif remark.strip().lower() == 'accepted':
        return "Accepted", "green"
    elif remark.strip().lower() == 'rejected':
        return "Improve and Resubmit", "orange"
    else:
        return "Under Review", "pink"

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
col1, col2 = st.columns([12, 1])
with col1:
    st.info("Please click adjacent refresh button to refresh the app")

with col2:
    if st.button("↻", help="Click to refresh"):
        st.session_state["college_select"] = "-- Select College --"

college_list = ['-- Select College --'] + df['college_name'].dropna().unique().tolist()
selected_college = st.selectbox("College Names", sorted(college_list), index=0, key="college_select")
if selected_college == '-- Select College --':
    st.warning("Please select a college to view student assignments.")
    st.stop()

college_students = df[df['college_name'] == selected_college][['student_name', 'email']].dropna(subset=['student_name'])
students = college_students['student_name'].unique()

selected_student = st.selectbox("Student Names", sorted(students), key="student_select")

# Check if the selected student name appears more than once
student_entries = college_students[college_students['student_name'] == selected_student]

if len(student_entries) > 1:
    # Show dropdown of emails if multiple students with the same name
    selected_email = st.selectbox("Select Email ID", student_entries['email'].unique(), key="email_select")
else:
    selected_email = student_entries['email'].iloc[0]

assignment_list = list(list_of_assignments.keys())
selected_assignment = st.selectbox("Assignment Names", assignment_list, key="assignment_select")

status_col = list_of_assignments[selected_assignment]["status"]
comment_col = list_of_assignments[selected_assignment]["comment"]

if len(student_entries) > 1:
    student_row = df[(df['college_name'] == selected_college) &
                     (df['student_name'] == selected_student) &
                     (df['email'] == selected_email)]
else:
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
    if st.button("Show Assignment Status"):
        st.markdown(f"<div class='status-box status-{status_color}'>{status_text}</div>", unsafe_allow_html=True)
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

        time = datetime.now(pytz.timezone('Asia/Kolkata'))
        timestamp = time.strftime('%d-%m-%Y %H:%M:%S')
        log_row = [timestamp, selected_college, selected_student, selected_assignment, status_text, "Viewed", current_feedback or "No feedback Provided"]
        try:
            sheet.append_row(log_row)
        except Exception as e:
            st.error(f"Could not log activity: {str(e)}")

    feedback_str = f"Student: {selected_student}\nCollege: {selected_college}\nAssignment: {selected_assignment}\nStatus: {status_text}\n\n"    
    feedback_str += f"Current Feedback:\n{current_feedback if current_feedback else 'No feedback provided.'}\n\n"
    feedback_str += f"Feedback History:\n{feedback_history if feedback_history else 'No feedback history available.'}"

    download_clicked = st.download_button("Download Complete Feedback",feedback_str,file_name=f"{selected_student}_{selected_assignment}_feedback.txt")
    if download_clicked:
        time = datetime.now(pytz.timezone('Asia/Kolkata'))
        timestamp = time.strftime('%d-%m-%Y %H:%M:%S')
        log_row = [timestamp, selected_college, selected_student, selected_assignment, status_text, "Downloaded", current_feedback or "No feedback Provided"]
        try:
            sheet.append_row(log_row)
        except Exception as e:
            st.error(f"Could not log activity: {str(e)}")

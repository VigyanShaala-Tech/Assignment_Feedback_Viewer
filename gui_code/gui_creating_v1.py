import streamlit as st
import pandas as pd
import re
from PIL import Image

st.markdown(
    """
    <style>
    html, body, .stApp {
        height: 100%;
        margin: 0;
        padding: 0;
        background-color: #e6ffe6;
    }

    header, .css-18ni7ap {
        background: transparent !important;
        box-shadow: none
    }

    .status-box {
        padding: 0.75rem 1rem;
        border-radius: 8px;
        font-weight: bold;
        display: inline-block;
        margin-top: 0.5rem;
        color: #000000;
        border: 1px solid transparent;
    }

    .status-red {
        background-color: rgba(255, 77, 77, 0.2);
        border-color: rgba(255, 77, 77, 0.6);
        color: #cc0000;
    }

    .status-green {
        background-color: rgba(40, 167, 69, 0.2);
        border-color: rgba(40, 167, 69, 0.6);
        color: #1e6f3d;
    }

    .status-orange {
        background-color: rgba(255, 165, 0, 0.2);
        border-color: rgba(255, 165, 0, 0.6);
        color: #cc8400;
    }

    .status-pink {
        background-color: rgba(255, 105, 180, 0.2);
        border-color: rgba(255, 105, 180, 0.6);
        color: #c94c9d;
    }
    </style>
    """,
    unsafe_allow_html=True
)

co1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("gui_code/VS-logo.png", width=150)

df = pd.read_csv("gui_code/For-Sharing_Student_Assignment_Status-_-Feedback-sheet.csv")

# Mapping of assignment-names to their respective status and comment columns
list_of_assignments = {
    "Goal Setting": {
        "status": "Assignment_Goal_setting",
        "comment": "Comments_Assignment_Goal_setting"
    },
    "LinkedIn Profile": {
        "status": "Assignment_LinkedIn_Profile",
        "comment": "Comments_Assignment_LinkedIn_Profile"
    },
    "STEM Curiosity": {
        "status": "Assignment_STEM_Curiosity",
        "comment": "Comments_Assignment_STEM_Curiosity"
    },
    "Career Journal": {
        "status": "Assignment_Career_Journal",
        "comment": "Comments_Assignment_Career_Journal"
    }
}

def get_status(remark):
    if remark.strip().lower() == 'no submission':
        return "Not Submitted", "red"
    elif remark.strip().lower() == 'accepted':
        return "Assignment Accepted", "green"
    elif remark.strip().lower() == 'rejected with feedback':
        return "Rejected With Feedback", "orange"
    else:
        return 'Under Review', 'Pink'

def clean_line_end(line):
    if isinstance(line, str):
        # Removing non-ASCII characters like _x000D_
        cleaned = re.sub(r'[^\x00-\x7F]+', '', line)
        # To Remove specific encoding artifacts like _x000D_
        cleaned = re.sub(r'_x[0-9A-Fa-f]{4}_', '', cleaned)
        # To Remove all special characters except alphanumeric, spaces, periods, and the # symbol
        cleaned = re.sub(r'[^a-zA-Z0-9\s.#]', '', cleaned)
        # Collapse multiple spaces into a single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # Removing leading and trailing whitespace
        return cleaned.strip()
    return line

def parse_feedback(comment):
    if pd.isna(comment) or not comment:
        return "", ""
    cleaned_comment = clean_line_end(comment)
    # 1. Counting the number of '#' symbols
    hash_count = cleaned_comment.count('#')
    # 2. Split by '#', to get byparts
    parts = cleaned_comment.split('#')
    # Removing empty elements
    parts = [part.strip() for part in parts if part.strip()]
    # Counting the number of paragraphs after splitting
    num_parts = len(parts)
    if num_parts == 0:
        # No content after cleaning
        return "", ""
    elif hash_count == 1:
        # case: If there's exactly one # symbol, everything will go to current feedback
        return "", cleaned_comment
    else:
        # The last part goes to current feedback, all others to history
        history = ' # '.join(parts[:-1])
        current = parts[-1]
        return history, current

st.title(" Assignment Feedback Viewer")
college_list = df['Filter out your college name here'].dropna().unique()
selected_college = st.selectbox("College_Names", sorted(college_list))

students = df[df['Filter out your college name here'] == selected_college]['Student Name'].dropna().unique()
selected_student = st.selectbox("Student_Names", sorted(students))

assignment_list = list(list_of_assignments.keys())
selected_assignment = st.selectbox("Assignment_Names", assignment_list)
status_col = list_of_assignments[selected_assignment]["status"]
comment_col = list_of_assignments[selected_assignment]["comment"]

student_row = df[(df['Filter out your college name here'] == selected_college) &
                 (df['Student Name'] == selected_student)]

if student_row.empty:
    st.warning("No data found for the selected combination.")
else:
    assignment_status = student_row.iloc[0][status_col]
    comment = student_row.iloc[0][comment_col]
    
    status_text, status_color = get_status(assignment_status)

    feedback_history, current_feedback = parse_feedback(comment)

st.markdown(f"### Assignment: {selected_assignment}")
st.markdown(f"**Status:** <span style='color:{status_color}; font-weight:bold;'>{status_text}</span>", unsafe_allow_html=True)
    
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

feedback_str = f"Student: {selected_student}\nCollege: {selected_college}\nAssignment: {selected_assignment}\nStatus: {status_text}\n\n"    
feedback_str = feedback_str + f"Current Feedback:\n{current_feedback if current_feedback else 'No feedback provided.'}\n\n"
feedback_str = feedback_str + f"Feedback History:\n{feedback_history if feedback_history else 'No feedback history available.'}"
    
st.download_button("Download Complete Feedback", feedback_str,file_name=f"{selected_student}_{selected_assignment}_feedback.txt")

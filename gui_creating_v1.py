import streamlit as st
import pandas as pd

df = pd.read_csv("/home/arjun/Assignment_Feedback_Viewer/For-Sharing_Student_Assignment_Status-_-Feedback-sheet.csv")

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

college_list = df['Filter out your college name here'].dropna().unique()
selected_college = st.sidebar.selectbox("College_Names", sorted(college_list))

students = df[df['Filter out your college name here'] == selected_college]['Student Name'].dropna().unique()
selected_student = st.sidebar.selectbox("Student_Names", sorted(students))

assignment_list = list(list_of_assignments.keys())
selected_assignment = st.sidebar.selectbox("Assignment_Names", assignment_list)

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
    
    if not pd.isna(comment):
        paragraphs = comment.split('\n')
        current_feedback = paragraphs[0] if paragraphs else ""
        history = '\n'.join(paragraphs[1:]) if len(paragraphs) > 1 else ""
    else:
        current_feedback = ""
        history = ""
    
    st.title("📄 Assignment Feedback Viewer")
    st.markdown(f"### Assignment: {selected_assignment}")
    st.markdown(f"**Status:** <span style='color:{status_color}; font-weight:bold;'>{status_text}</span>", unsafe_allow_html=True)
    
    st.markdown("### Current Feedback:")
    if not current_feedback:
        st.info("No feedback provided yet.")
    else:
        st.text(current_feedback)
    
    st.markdown("### Feedback History:")
    if not history:
        st.info("No feedback history available.")
    else:
        st.text(history)
    
    feedback_str = f"Assignment: {selected_assignment}\nStatus: {status_text}\n\n"
    feedback_str += f"Current Feedback:\n{current_feedback if current_feedback else 'No feedback provided.'}\n\n"
    feedback_str += f"Feedback History:\n{history if history else 'No feedback history available.'}"
    
    st.download_button("Download Complete Feedback", feedback_str, file_name=f"{selected_student}_{selected_assignment}_feedback.txt")
    

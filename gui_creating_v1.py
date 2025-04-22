import streamlit as st
import pandas as pd
df = pd.read_csv("/home/arjun/Assignment_Feedback_Viewer/For-Sharing_Student_Assignment_Status-_-Feedback-sheet.csv")

# Splitted the multiple assignment_names into a dictionary
list_of_assignments = {
    "Goal Setting": ("Assignment_Goal_setting", "Comments_Assignment_Goal_setting"),
    "LinkedIn Profile": ("Assignment_LinkedIn_Profile", "Comments_Assignment_LinkedIn_Profile"),
    "STEM Curiosity": ("Assignment_STEM_Curiosity", "Comments_Assignment_STEM_Curiosity"),
    "Career Journal": ("Assignment_Career_Journal", "Comments_Assignment_Career_Journal"),
}
#Below function is used to get the status of the assignment based on the comment
def get_status(comment):
    if pd.isna(comment) or comment == 'No submission':
        return "Not Submiited", "red"
    elif comment =='Accepted':
        return "Assignment Accepted", "green"
    else:
        return "REJECTED WITH FEEDBACK", "orange"

# Getting the list of colleges from the dataframe
college_list = df['Filter out your college name here'].dropna().unique()
selected_college = st.sidebar.selectbox("College Names", sorted(college_list))

# Getting the list of students from the selected college
students = df[df['Filter out your college name here'] == selected_college]['Student Name'].dropna().unique()
selected_student = st.sidebar.selectbox("Student Name", sorted(students))

assignment_list = list(list_of_assignments.keys())
selected_assignment = st.sidebar.selectbox("Assignment Name", assignment_list)

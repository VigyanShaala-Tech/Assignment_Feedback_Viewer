import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os, textwrap
from datetime import datetime
import pytz

# ---------------------------------------------------
# Load environment variables + create DB engine
# ---------------------------------------------------
load_dotenv("config.env")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
COHORT_CODE = os.getenv("COHORT_CODE")


engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ---------------- SESSION STATE INITIALIZATION ----------------

if "prev_assignment" not in st.session_state:
    st.session_state.prev_assignment = None

if "show_status" not in st.session_state:
    st.session_state.show_status = False

if "view_logged" not in st.session_state:
    st.session_state.view_logged = False


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
    st.image(r"C:\Assignment_Feedback_UI\Assignment_Feedback_Viewer\gui_code\log.png", width=350)


# ---------------------------------------------------
# SQL Queries (For each UI element)
# ---------------------------------------------------


Query_Colleges = text(textwrap.dedent("""
    SELECT DISTINCT 
    cm.standard_college_names AS college_name
    FROM raw.student_education se
    INNER JOIN raw.student_cohort sc
    ON se.student_id = sc.student_id
    LEFT JOIN raw.college_mapping cm
    ON se.college_id = cm.college_id 
    WHERE sc.cohort_code = :cohort_code
        AND cm.standard_college_names IS NOT NULL
    ORDER BY cm.standard_college_names;
"""))


# Students for selected college
QUERY_STUDENTS = text(textwrap.dedent("""
    WITH filtered_students AS (
        SELECT DISTINCT
            se.student_id
        FROM raw.student_education se
        INNER JOIN raw.college_mapping cm
            ON se.college_id = cm.college_id
        WHERE cm.standard_college_names = :college
    )

    SELECT 
        sd.id AS student_id,
        concat_ws(' ',
            trim(sd.first_name),
            trim(sd.last_name)
        ) AS student_name,
        email
    FROM raw.student_details sd
    INNER JOIN filtered_students fs
        ON sd.id = fs.student_id
    WHERE sd.first_name IS NOT NULL
      AND sd.last_name IS NOT NULL
    ORDER BY student_name;
"""))


# Assignments for selected student
QUERY_ASSIGNMENTS = text(textwrap.dedent("""
    SELECT
        sa.student_id,
        sa.resource_id,
        r.title AS resource_title,
        sa.submission_status,
        sa.marks_pct,
        sa.feedback_comments,
        sa.submitted_at
    FROM raw.student_assignment sa
    INNER JOIN raw.resource r
        ON sa.resource_id = r.id
    WHERE sa.student_id = :student_id
    ORDER BY sa.submitted_at DESC;
"""))

# Latest status + comment
QUERY_LATEST_STATUS = text(textwrap.dedent("""
    SELECT submission_status, feedback_comments, submitted_at
    FROM raw.student_assignment
    WHERE student_id = :student_id
      AND resource_id = :resource_id
    ORDER BY submitted_at DESC
    LIMIT 1;
"""))

QUERY_FEEDBACK_HISTORY = text(textwrap.dedent("""
    SELECT
        submission_status,
        feedback_comments,
        submitted_at
    FROM raw.student_assignment
    WHERE student_id = :student_id
      AND resource_id = :resource_id
    ORDER BY submitted_at DESC
    OFFSET 1;
"""))

QUERY_INSERT_ACTIVITY = text("""
    INSERT INTO old.activity_log (
        activity_time,
        college_name,
        student_name,
        assignment_name,
        assignment_status,
        action,
        feedback
    )
    VALUES (
        :activity_time,
        :college_name,
        :student_name,
        :assignment_name,
        :assignment_status,
        :action,
        :feedback
    );
""")

# ---------------------------------------------------
# Helper Functions
# ---------------------------------------------------

def get_colleges():
    with engine.begin() as conn:
        result = conn.execute(Query_Colleges,{"cohort_code": COHORT_CODE})
        return [row.college_name for row in result]
    
def get_students(college):
    with engine.begin() as conn:
        return pd.read_sql(QUERY_STUDENTS,conn,params={"college": college})

def get_assignments(student_id):
    student_id = int(student_id)
    with engine.begin() as conn:
        return pd.read_sql(QUERY_ASSIGNMENTS,conn,params={"student_id": student_id})

def get_latest_assignment_status(student_id, resource_id):
    with engine.begin() as conn:
        return pd.read_sql(QUERY_LATEST_STATUS,conn,params={"student_id": int(student_id),"resource_id": int(resource_id)})

def get_status(remark):
    if not remark:
        return "Under Review", "gray"

    remark_clean = remark.strip().lower()

    status_map = {
        "not submitted": ("Not Submitted", "red"),
        "accepted": ("Accepted", "green"),
        "rejected": ("Improve and Resubmit", "orange"),
        "submitted": ("Under Review", "blue"),
        "pending": ("Under Review", "pink"),
    }

    return status_map.get(
        remark_clean,
        ("Under Review", "gray")
    )

def get_feedback_history(student_id, resource_id):
    with engine.begin() as conn:
        return pd.read_sql(QUERY_FEEDBACK_HISTORY,conn,params={"student_id": int(student_id),"resource_id": int(resource_id)})

# ---------------------------------------------------
# STREAMLIT UI
# ---------------------------------------------------
st.title(" Assignment Feedback Viewer")

#Splits the page horizontally into two columns.
col1, col2 = st.columns([12, 1])
with col1:
    st.info("Please click adjacent refresh button to refresh the app")

with col2:
    if st.button("↻", help="Click to refresh"):
        st.session_state["college_select"] = "-- Select College --"

# ----------------- Select College -----------------

college_list = ["-- Select College --"] + get_colleges()

selected_college = st.selectbox("College Names", college_list, key="college_select")

if selected_college == "-- Select College --":
    st.warning("Please select a college to view student assignments.")
    st.stop()

# ----------------- Select Student -----------------


students_df = get_students(selected_college)
student_list = ["-- Select Student --"] + sorted(students_df["student_name"].dropna().unique().tolist())

selected_student = st.selectbox("Student Names", student_list)

if selected_student == "-- Select Student --":
    st.stop()

matched_students = students_df[
    students_df["student_name"] == selected_student]

if len(matched_students) > 1:
   

    email_list = ["-- Select Email --"] + matched_students["email"].tolist()

    selected_email = st.selectbox(
        "Select Email ID",
        email_list
    )

    if selected_email == "-- Select Email --":
        st.stop()

    student_id = matched_students.loc[
        matched_students["email"] == selected_email,
        "student_id"
    ].iloc[0]

else:
    # Only one student
    student_id = matched_students["student_id"].iloc[0]


# ----------------- Select Assignment -----------------


assignments_df = get_assignments(student_id)
assignment_list = ["-- Select Assignment --"] + assignments_df["resource_title"].unique().tolist()

selected_assignment = st.selectbox("Assignment Names", assignment_list)

if selected_assignment == "-- Select Assignment --":
    st.stop()

if st.session_state.prev_assignment != selected_assignment:
    st.session_state.prev_assignment = selected_assignment
    st.session_state.show_status = False
    st.session_state.view_logged = False
resource_id = assignments_df.loc[assignments_df["resource_title"] == selected_assignment,"resource_id"].iloc[0]

#------------------ Select Submission Status --------------

if "show_status" not in st.session_state:
    st.session_state.show_status = False

st.markdown(
    f"<h5 style='margin-bottom:4px;'> Assignment: {selected_assignment}</h5>",
    unsafe_allow_html=True
)


if st.button("Show Assignment Status"):
    st.session_state.show_status = True
    
latest = None
status_text = None
feedback_str = ""

if st.session_state.show_status:
    status_df = get_latest_assignment_status(student_id, resource_id)

    if status_df.empty:
        st.warning("No submission found for this assignment.")
        st.stop()

    latest = status_df.iloc[0]

    # ---------- STATUS BADGE ----------
    status_text, color = get_status(latest["submission_status"])

    st.session_state.viewed_status = status_text
    st.session_state.viewed_feedback = latest["feedback_comments"] or "No feedback provided"

    st.markdown(
        f"""
        <div style="
            padding:10px 14px;
            border-radius:8px;
            background-color:{color};
            color:white;
            font-weight:bold;
            width:fit-content;
            margin-bottom:10px;
        ">
            {status_text}
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------- FEEDBACK ----------
    st.markdown(
        f"<h5 style='margin-bottom:4px;'> Current Feedback:</h5>",
        unsafe_allow_html=True
    )
    st.write(
        latest["feedback_comments"]
        if latest["feedback_comments"]
        else "No feedback provided yet."
    )


    activity_time = datetime.now(pytz.timezone("Asia/Kolkata")).replace(tzinfo=None)

    if not st.session_state.get("view_logged", False):
        with engine.begin() as conn:
            conn.execute(
                QUERY_INSERT_ACTIVITY,
                {
                    "activity_time": activity_time,
                    "college_name": selected_college,
                    "student_name": selected_student,
                    "assignment_name": selected_assignment,
                    "assignment_status": status_text,
                    "action": "Viewed",
                    "feedback": latest["feedback_comments"] or "No feedback provided"
                }
            )

        st.session_state.view_logged = True

#------- SELECT HISTORY FEEDBACK ---------

    history_df = get_feedback_history(student_id, resource_id)

    st.markdown(f"<h5 style='margin-bottom:4px;'> Feedback History:</h5>",unsafe_allow_html=True)

    feedback_no = 1
    if history_df.empty:
        st.caption("No previous feedback available.")
    else:
        for _, row in history_df.iterrows():
            status_text, _ = get_status(row["submission_status"])
            if status_text != "Under Review":
                st.write(f"Feedback {feedback_no}:")
                st.write(row["feedback_comments"] or "No feedback provided.")
                feedback_no += 1

feedback_str = ""  # IMPORTANT: initialize as string

if latest is not None:
    feedback_str = f"""
College: {selected_college}
Student: {selected_student}
Assignment: {selected_assignment}

Latest Status: {status_text}
Latest Feedback:
{latest["feedback_comments"] or "No feedback provided."}

Previous Feedback:
"""

    if history_df.empty:
        feedback_str += "No previous feedback available.\n"
    else:
        for _, row in history_df.iterrows():
            hist_status, _ = get_status(row["submission_status"])

            feedback_str += f"\nStatus: {hist_status}\n"
            feedback_str += f"Submitted At: {row['submitted_at']}\n"

            #  SAME RULE AS UI
            if hist_status != "Under Review":
                feedback_str += "Feedback:\n"
                feedback_str += (row["feedback_comments"] or "No feedback provided.") + "\n"

            feedback_str += "-" * 25 + "\n"

if st.session_state.show_status:
    download_clicked = st.download_button(
        "Download Complete Feedback",
        feedback_str,
        file_name=f"{selected_student}_{selected_assignment}_feedback.txt"
    )

    if download_clicked:
        activity_time = datetime.now(pytz.timezone("Asia/Kolkata")).replace(tzinfo=None)

        try:
            with engine.begin() as conn:
                conn.execute(
                    QUERY_INSERT_ACTIVITY,
                    {
                        "activity_time": activity_time,
                        "college_name": selected_college,
                        "student_name": selected_student,
                        "assignment_name": selected_assignment,
                        "assignment_status": st.session_state.viewed_status,
                        "action": "Downloaded", 
                        "feedback": st.session_state.viewed_feedback
                    }
                )
        except Exception as e:
            st.error(f"Could not log activity: {str(e)}")

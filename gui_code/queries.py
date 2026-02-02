# queries.py
from sqlalchemy import text
import textwrap

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
-- ============================================================
-- EduShield
-- 03_post_load_audit.sql
-- ============================================================

USE edushield;

-- ------------------------------------------------------------
-- Row counts
-- ------------------------------------------------------------

SELECT 'academic_terms' AS table_name, COUNT(*) AS row_count FROM academic_terms
UNION ALL
SELECT 'departments', COUNT(*) FROM departments
UNION ALL
SELECT 'majors', COUNT(*) FROM majors
UNION ALL
SELECT 'instructors', COUNT(*) FROM instructors
UNION ALL
SELECT 'students', COUNT(*) FROM students
UNION ALL
SELECT 'courses', COUNT(*) FROM courses
UNION ALL
SELECT 'course_offerings', COUNT(*) FROM course_offerings
UNION ALL
SELECT 'assignments', COUNT(*) FROM assignments
UNION ALL
SELECT 'submissions', COUNT(*) FROM submissions
UNION ALL
SELECT 'detector_tools', COUNT(*) FROM detector_tools
UNION ALL
SELECT 'ai_detector_results', COUNT(*) FROM ai_detector_results
UNION ALL
SELECT 'student_behavior_events', COUNT(*) FROM student_behavior_events
UNION ALL
SELECT 'integrity_cases', COUNT(*) FROM integrity_cases
UNION ALL
SELECT 'student_integrity_history', COUNT(*) FROM student_integrity_history;

-- ------------------------------------------------------------
-- Target distribution
-- ------------------------------------------------------------

SELECT
    is_ai_generated,
    COUNT(*) AS submission_count,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM submissions),
        2
    ) AS percentage
FROM submissions
GROUP BY is_ai_generated
ORDER BY is_ai_generated;

-- ------------------------------------------------------------
-- Orphan checks
-- ------------------------------------------------------------

SELECT 'submissions -> students' AS check_name, COUNT(*) AS orphan_count
FROM submissions s
LEFT JOIN students st
    ON s.student_id = st.student_id
WHERE st.student_id IS NULL

UNION ALL

SELECT 'submissions -> assignments', COUNT(*)
FROM submissions s
LEFT JOIN assignments a
    ON s.assignment_id = a.assignment_id
WHERE a.assignment_id IS NULL

UNION ALL

SELECT 'assignments -> offerings', COUNT(*)
FROM assignments a
LEFT JOIN course_offerings o
    ON a.offering_id = o.offering_id
WHERE o.offering_id IS NULL

UNION ALL

SELECT 'offerings -> courses', COUNT(*)
FROM course_offerings o
LEFT JOIN courses c
    ON o.course_id = c.course_id
WHERE c.course_id IS NULL

UNION ALL

SELECT 'offerings -> terms', COUNT(*)
FROM course_offerings o
LEFT JOIN academic_terms t
    ON o.term_id = t.term_id
WHERE t.term_id IS NULL

UNION ALL

SELECT 'offerings -> instructors', COUNT(*)
FROM course_offerings o
LEFT JOIN instructors i
    ON o.instructor_id = i.instructor_id
WHERE i.instructor_id IS NULL

UNION ALL

SELECT 'detector_results -> submissions', COUNT(*)
FROM ai_detector_results d
LEFT JOIN submissions s
    ON d.submission_id = s.submission_id
WHERE s.submission_id IS NULL

UNION ALL

SELECT 'detector_results -> tools', COUNT(*)
FROM ai_detector_results d
LEFT JOIN detector_tools t
    ON d.tool_id = t.tool_id
WHERE t.tool_id IS NULL

UNION ALL

SELECT 'history -> students', COUNT(*)
FROM student_integrity_history h
LEFT JOIN students s
    ON h.student_id = s.student_id
WHERE s.student_id IS NULL;

-- ------------------------------------------------------------
-- Duplicate business-key checks
-- ------------------------------------------------------------

SELECT
    student_id,
    assignment_id,
    COUNT(*) AS duplicate_count
FROM submissions
GROUP BY student_id, assignment_id
HAVING COUNT(*) > 1;

-- ------------------------------------------------------------
-- Detector coverage
-- ------------------------------------------------------------

SELECT
    COUNT(DISTINCT submission_id) AS submissions_with_detector_results,
    COUNT(DISTINCT tool_id) AS detector_tools_used,
    COUNT(*) AS detector_result_rows
FROM ai_detector_results;

-- ------------------------------------------------------------
-- Timeline checks
-- ------------------------------------------------------------

SELECT COUNT(*) AS impossible_submission_times
FROM submissions s
JOIN assignments a
    ON s.assignment_id = a.assignment_id
WHERE s.submitted_at < a.assignment_open_at;

SELECT COUNT(*) AS detector_before_submission
FROM ai_detector_results d
JOIN submissions s
    ON d.submission_id = s.submission_id
WHERE d.test_timestamp <= s.submitted_at;

SELECT COUNT(*) AS invalid_case_chronology
FROM integrity_cases
WHERE
    (case_open_date IS NOT NULL AND incident_date IS NOT NULL
     AND case_open_date < incident_date)
    OR
    (case_closed_date IS NOT NULL AND case_open_date IS NOT NULL
     AND case_closed_date < case_open_date);

-- ============================================================
-- EduShield
-- 04_create_reporting_views.sql
-- ============================================================
-- Reporting layer for Power BI.
--
-- These views sit above the normalized MySQL tables and provide
-- analytics-ready datasets without changing the underlying model.
--
-- Recommended Power BI usage:
--   vw_submission_analytics      -> primary submission fact
--   vw_detector_analysis         -> detector-level fact
--   vw_student_integrity_profile -> student-level profile
--   vw_assignment_analytics      -> assignment-level analysis
--   vw_integrity_case_analysis   -> integrity case analysis
--   vw_behavior_event_analysis   -> behavior-event analysis
--
-- Requires MySQL 8.0+ for CTEs/window functions.
-- ============================================================

USE edushield;

-- ============================================================
-- 1. SUBMISSION ANALYTICS
-- Grain: exactly one row per submission
-- ============================================================

DROP VIEW IF EXISTS vw_submission_analytics;

CREATE VIEW vw_submission_analytics AS
WITH detector_summary AS
(
    SELECT
        d.submission_id,

        COUNT(*) AS detector_result_count,

        COUNT(DISTINCT d.tool_id) AS detectors_available,

        SUM(
            CASE
                WHEN d.detected_as_ai = 1 THEN 1
                ELSE 0
            END
        ) AS detectors_detecting_ai,

        SUM(
            CASE
                WHEN UPPER(COALESCE(d.processing_status, ''))
                     = 'SUCCESS'
                THEN 1
                ELSE 0
            END
        ) AS successful_detector_count,

        AVG(d.ai_probability)
            AS mean_detector_ai_probability,

        MAX(d.ai_probability)
            AS max_detector_ai_probability,

        MIN(d.ai_probability)
            AS min_detector_ai_probability,

        STDDEV_POP(d.ai_probability)
            AS detector_disagreement,

        AVG(d.confidence_score)
            AS mean_detector_confidence,

        MAX(d.confidence_score)
            AS max_detector_confidence

    FROM ai_detector_results d
    GROUP BY d.submission_id
),

behavior_summary AS
(
    SELECT
        s.submission_id,

        COUNT(e.event_id)
            AS prior_total_integrity_events,

        SUM(
            CASE
                WHEN e.event_date >=
                     DATE_SUB(s.submitted_at, INTERVAL 30 DAY)
                THEN 1
                ELSE 0
            END
        ) AS prior_30d_integrity_events,

        SUM(
            CASE
                WHEN e.event_date >=
                     DATE_SUB(s.submitted_at, INTERVAL 90 DAY)
                THEN 1
                ELSE 0
            END
        ) AS prior_90d_integrity_events,

        SUM(
            CASE
                WHEN e.event_type = 'AI Detector Flag'
                THEN 1
                ELSE 0
            END
        ) AS prior_ai_detector_flags,

        SUM(
            CASE
                WHEN e.event_type = 'Similarity Flag'
                THEN 1
                ELSE 0
            END
        ) AS prior_similarity_flags,

        SUM(
            CASE
                WHEN e.event_type = 'Unusual Collaboration'
                THEN 1
                ELSE 0
            END
        ) AS prior_collaboration_flags,

        SUM(
            CASE
                WHEN e.event_type = 'Rapid Submission'
                THEN 1
                ELSE 0
            END
        ) AS prior_rapid_submission_flags,

        SUM(
            CASE
                WHEN e.event_type = 'Plagiarism Flag'
                THEN 1
                ELSE 0
            END
        ) AS prior_plagiarism_flags,

        SUM(
            CASE
                WHEN e.event_type = 'Excessive Copy-Paste'
                THEN 1
                ELSE 0
            END
        ) AS prior_copy_paste_flags,

        SUM(
            CASE
                WHEN e.event_type = 'Repeated Revision Anomaly'
                THEN 1
                ELSE 0
            END
        ) AS prior_revision_anomalies,

        SUM(
            CASE
                WHEN e.event_type = 'Peer Report'
                THEN 1
                ELSE 0
            END
        ) AS prior_peer_reports,

        SUM(
            CASE
                WHEN e.event_type = 'Unauthorized File Sharing'
                THEN 1
                ELSE 0
            END
        ) AS prior_file_sharing_events

    FROM submissions s
    LEFT JOIN student_behavior_events e
        ON e.student_id = s.student_id
       AND e.event_date < s.submitted_at

    GROUP BY s.submission_id
),

history_ranked AS
(
    SELECT
        s.submission_id,
        h.history_id,
        h.snapshot_at,
        h.integrity_score,
        h.trust_factor_score,
        h.prior_confirmed_cases,
        h.prior_dismissed_cases,
        h.prior_suspicious_flags,
        h.prior_ai_flags,
        h.prior_plagiarism_flags,
        h.prior_sanction_points,
        h.recent_integrity_events,
        h.integrity_status,

        ROW_NUMBER() OVER
        (
            PARTITION BY s.submission_id
            ORDER BY h.snapshot_at DESC
        ) AS rn

    FROM submissions s
    LEFT JOIN student_integrity_history h
        ON h.student_id = s.student_id
       AND h.snapshot_at < s.submitted_at
)

SELECT

    -- --------------------------------------------------------
    -- Submission identifiers
    -- --------------------------------------------------------

    s.submission_id,
    s.student_id,
    s.assignment_id,

    -- --------------------------------------------------------
    -- Academic context
    -- --------------------------------------------------------

    a.assignment_title,
    a.assignment_type,
    a.difficulty_level AS assignment_difficulty,
    a.expected_word_count,
    a.max_word_count,
    a.prompt_complexity,
    a.open_endedness,
    a.research_intensity,
    a.rubric_specificity,
    a.requires_citations,
    a.required_references,
    a.research_required,
    a.oral_defense_required,
    a.collaboration_allowed,
    a.allowed_ai_usage,
    a.design_type,

    o.offering_id,
    o.section_code,
    o.class_size,
    o.delivery_mode,

    c.course_id,
    c.course_code,
    c.course_name,
    c.subject_area,
    c.course_level,
    c.difficulty_level AS course_difficulty,
    c.credits,

    t.term_id,
    t.term_name,
    t.academic_year,
    t.term_type,

    i.instructor_id,
    i.instructor_name,
    i.academic_rank,
    i.years_experience,
    i.teaching_load,
    i.ai_policy_adoption,

    dept.department_id,
    dept.department_name,

    -- --------------------------------------------------------
    -- Student profile
    -- --------------------------------------------------------

    st.first_name,
    st.last_name,
    CONCAT(
        st.first_name,
        ' ',
        st.last_name
    ) AS student_name,

    st.gender,
    st.year_level,
    st.major_id,
    m.major_name,
    st.gpa,
    st.attendance_rate,
    st.academic_standing,
    st.scholarship_status,
    st.active_status AS student_active_status,

    -- --------------------------------------------------------
    -- Submission behavior
    -- --------------------------------------------------------

    s.submitted_at,
    s.submission_status,
    s.word_count,
    s.cited_references,
    s.similarity_score,
    s.late_submission,
    s.hours_before_deadline,

    s.editing_sessions,
    s.revision_count,
    s.draft_count,
    s.time_spent_minutes,
    s.copy_paste_ratio,
    s.number_of_edits,

    s.typing_consistency,
    s.avg_sentence_length,
    s.sentence_length_std,
    s.vocabulary_richness,
    s.lexical_diversity,
    s.repetition_ratio,
    s.paragraph_count,
    s.grammar_error_rate,
    s.citation_density,
    s.semantic_coherence,
    s.perplexity_score,
    s.burstiness_score,

    -- --------------------------------------------------------
    -- Outcome / target
    -- --------------------------------------------------------

    s.grade,
    s.feedback_score,
    s.is_ai_generated,
    s.ai_generation_source,

    -- --------------------------------------------------------
    -- Detector ensemble
    -- --------------------------------------------------------

    COALESCE(
        ds.detector_result_count,
        0
    ) AS detector_result_count,

    COALESCE(
        ds.detectors_available,
        0
    ) AS detectors_available,

    COALESCE(
        ds.detectors_detecting_ai,
        0
    ) AS detectors_detecting_ai,

    COALESCE(
        ds.successful_detector_count,
        0
    ) AS successful_detector_count,

    ds.mean_detector_ai_probability,
    ds.max_detector_ai_probability,
    ds.min_detector_ai_probability,

    CASE
        WHEN ds.mean_detector_ai_probability IS NOT NULL
        THEN
            ds.mean_detector_ai_probability
            - 0.50
        ELSE NULL
    END AS detector_mean_deviation_from_midpoint,

    ds.detector_disagreement,
    ds.mean_detector_confidence,
    ds.max_detector_confidence,

    CASE
        WHEN ds.detectors_available > 0
        THEN
            ds.detectors_detecting_ai
            / ds.detectors_available
        ELSE NULL
    END AS detector_ai_flag_rate,

    CASE
        WHEN ds.detector_result_count > 0
        THEN
            ds.successful_detector_count
            / ds.detector_result_count
        ELSE NULL
    END AS detector_success_rate,

    (
        ds.max_detector_ai_probability
        -
        ds.min_detector_ai_probability
    ) AS detector_probability_range,

    -- --------------------------------------------------------
    -- Historical behavior
    -- --------------------------------------------------------

    COALESCE(
        bs.prior_total_integrity_events,
        0
    ) AS prior_total_integrity_events,

    COALESCE(
        bs.prior_30d_integrity_events,
        0
    ) AS prior_30d_integrity_events,

    COALESCE(
        bs.prior_90d_integrity_events,
        0
    ) AS prior_90d_integrity_events,

    COALESCE(
        bs.prior_ai_detector_flags,
        0
    ) AS prior_ai_detector_flags,

    COALESCE(
        bs.prior_similarity_flags,
        0
    ) AS prior_similarity_flags,

    COALESCE(
        bs.prior_collaboration_flags,
        0
    ) AS prior_collaboration_flags,

    COALESCE(
        bs.prior_rapid_submission_flags,
        0
    ) AS prior_rapid_submission_flags,

    COALESCE(
        bs.prior_plagiarism_flags,
        0
    ) AS prior_plagiarism_flags,

    COALESCE(
        bs.prior_copy_paste_flags,
        0
    ) AS prior_copy_paste_flags,

    COALESCE(
        bs.prior_revision_anomalies,
        0
    ) AS prior_revision_anomalies,

    COALESCE(
        bs.prior_peer_reports,
        0
    ) AS prior_peer_reports,

    COALESCE(
        bs.prior_file_sharing_events,
        0
    ) AS prior_file_sharing_events,

    -- --------------------------------------------------------
    -- Historical integrity snapshot
    -- --------------------------------------------------------

    hr.snapshot_at AS historical_snapshot_at,
    hr.integrity_score AS historical_integrity_score,
    hr.trust_factor_score AS historical_trust_factor_score,
    hr.prior_confirmed_cases,
    hr.prior_dismissed_cases,
    hr.prior_suspicious_flags,
    hr.prior_ai_flags,
    hr.prior_plagiarism_flags AS historical_prior_plagiarism_flags,
    hr.prior_sanction_points,
    hr.recent_integrity_events AS historical_recent_integrity_events,
    hr.integrity_status AS historical_integrity_status

FROM submissions s

LEFT JOIN assignments a
    ON s.assignment_id = a.assignment_id

LEFT JOIN course_offerings o
    ON a.offering_id = o.offering_id

LEFT JOIN courses c
    ON o.course_id = c.course_id

LEFT JOIN academic_terms t
    ON o.term_id = t.term_id

LEFT JOIN instructors i
    ON o.instructor_id = i.instructor_id

LEFT JOIN students st
    ON s.student_id = st.student_id

LEFT JOIN majors m
    ON st.major_id = m.major_id

LEFT JOIN departments dept
    ON c.department_id = dept.department_id

LEFT JOIN detector_summary ds
    ON s.submission_id = ds.submission_id

LEFT JOIN behavior_summary bs
    ON s.submission_id = bs.submission_id

LEFT JOIN history_ranked hr
    ON s.submission_id = hr.submission_id
   AND hr.rn = 1;


-- ============================================================
-- 2. DETECTOR ANALYSIS
-- Grain: one row per detector result
-- ============================================================

DROP VIEW IF EXISTS vw_detector_analysis;

CREATE VIEW vw_detector_analysis AS
SELECT

    d.detector_result_id,
    d.submission_id,
    d.tool_id,

    d.test_timestamp,
    d.ai_probability,
    d.confidence_score,
    d.detected_as_ai,
    d.writing_style_score,
    d.detector_perplexity_score,
    d.text_length,
    d.processing_status,

    dt.tool_name,
    dt.vendor,
    dt.model_version,
    dt.baseline_false_positive_rate,
    dt.baseline_false_negative_rate,
    dt.calibration_score,
    dt.active_status AS detector_active_status,

    s.student_id,
    CONCAT(
        st.first_name,
        ' ',
        st.last_name
    ) AS student_name,

    s.assignment_id,
    a.assignment_title,
    a.assignment_type,

    c.course_id,
    c.course_code,
    c.course_name,
    c.subject_area,

    t.term_id,
    t.term_name,
    t.academic_year,

    i.instructor_id,
    i.instructor_name,

    dept.department_id,
    dept.department_name,

    s.submitted_at,
    s.is_ai_generated

FROM ai_detector_results d

LEFT JOIN detector_tools dt
    ON d.tool_id = dt.tool_id

LEFT JOIN submissions s
    ON d.submission_id = s.submission_id

LEFT JOIN students st
    ON s.student_id = st.student_id

LEFT JOIN assignments a
    ON s.assignment_id = a.assignment_id

LEFT JOIN course_offerings o
    ON a.offering_id = o.offering_id

LEFT JOIN courses c
    ON o.course_id = c.course_id

LEFT JOIN academic_terms t
    ON o.term_id = t.term_id

LEFT JOIN instructors i
    ON o.instructor_id = i.instructor_id

LEFT JOIN departments dept
    ON c.department_id = dept.department_id;


-- ============================================================
-- 3. STUDENT INTEGRITY PROFILE
-- Grain: one row per student
-- ============================================================

DROP VIEW IF EXISTS vw_student_integrity_profile;

CREATE VIEW vw_student_integrity_profile AS
WITH latest_history AS
(
    SELECT
        h.*,

        ROW_NUMBER() OVER
        (
            PARTITION BY h.student_id
            ORDER BY h.snapshot_at DESC
        ) AS rn

    FROM student_integrity_history h
),

submission_summary AS
(
    SELECT
        s.student_id,

        COUNT(*) AS total_submissions,

        SUM(
            CASE
                WHEN s.is_ai_generated = 1 THEN 1
                ELSE 0
            END
        ) AS ai_generated_submissions

    FROM submissions s
    GROUP BY s.student_id
),

behavior_summary AS
(
    SELECT
        student_id,

        COUNT(*) AS total_behavior_events,

        SUM(
            CASE
                WHEN severity = 'High'
                THEN 1
                ELSE 0
            END
        ) AS high_severity_events,

        SUM(
            CASE
                WHEN event_type = 'AI Detector Flag'
                THEN 1
                ELSE 0
            END
        ) AS ai_detector_events,

        SUM(
            CASE
                WHEN event_type = 'Plagiarism Flag'
                THEN 1
                ELSE 0
            END
        ) AS plagiarism_events

    FROM student_behavior_events
    GROUP BY student_id
),

case_summary AS
(
    SELECT
        student_id,

        COUNT(*) AS total_integrity_cases,

        SUM(
            CASE
                WHEN verdict = 'Confirmed'
                THEN 1
                ELSE 0
            END
        ) AS confirmed_cases,

        SUM(
            CASE
                WHEN verdict = 'Dismissed'
                THEN 1
                ELSE 0
            END
        ) AS dismissed_cases,

        SUM(
            CASE
                WHEN ai_detector_flag = 1
                THEN 1
                ELSE 0
            END
        ) AS ai_detector_cases,

        SUM(
            CASE
                WHEN plagiarism_flag = 1
                THEN 1
                ELSE 0
            END
        ) AS plagiarism_cases,

        SUM(
            COALESCE(sanction_points, 0)
        ) AS total_sanction_points

    FROM integrity_cases
    GROUP BY student_id
)

SELECT

    st.student_id,
    CONCAT(
        st.first_name,
        ' ',
        st.last_name
    ) AS student_name,

    st.gender,
    st.year_level,
    st.gpa,
    st.attendance_rate,
    st.academic_standing,
    st.scholarship_status,
    st.active_status,

    m.major_id,
    m.major_name,

    dept.department_id,
    dept.department_name,

    COALESCE(
        ss.total_submissions,
        0
    ) AS total_submissions,

    COALESCE(
        ss.ai_generated_submissions,
        0
    ) AS ai_generated_submissions,

    CASE
        WHEN ss.total_submissions > 0
        THEN
            ss.ai_generated_submissions
            / ss.total_submissions
        ELSE NULL
    END AS ai_submission_rate,

    COALESCE(
        bs.total_behavior_events,
        0
    ) AS total_behavior_events,

    COALESCE(
        bs.high_severity_events,
        0
    ) AS high_severity_events,

    COALESCE(
        bs.ai_detector_events,
        0
    ) AS ai_detector_events,

    COALESCE(
        bs.plagiarism_events,
        0
    ) AS plagiarism_events,

    COALESCE(
        cs.total_integrity_cases,
        0
    ) AS total_integrity_cases,

    COALESCE(
        cs.confirmed_cases,
        0
    ) AS confirmed_cases,

    COALESCE(
        cs.dismissed_cases,
        0
    ) AS dismissed_cases,

    COALESCE(
        cs.ai_detector_cases,
        0
    ) AS ai_detector_cases,

    COALESCE(
        cs.plagiarism_cases,
        0
    ) AS plagiarism_cases,

    COALESCE(
        cs.total_sanction_points,
        0
    ) AS total_sanction_points,

    lh.snapshot_at AS latest_history_snapshot,
    lh.integrity_score,
    lh.trust_factor_score,
    lh.prior_confirmed_cases,
    lh.prior_dismissed_cases,
    lh.prior_suspicious_flags,
    lh.prior_ai_flags,
    lh.prior_plagiarism_flags,
    lh.prior_sanction_points,
    lh.recent_integrity_events,
    lh.integrity_status

FROM students st

LEFT JOIN majors m
    ON st.major_id = m.major_id

LEFT JOIN departments dept
    ON m.department_id = dept.department_id

LEFT JOIN submission_summary ss
    ON st.student_id = ss.student_id

LEFT JOIN behavior_summary bs
    ON st.student_id = bs.student_id

LEFT JOIN case_summary cs
    ON st.student_id = cs.student_id

LEFT JOIN latest_history lh
    ON st.student_id = lh.student_id
   AND lh.rn = 1;


-- ============================================================
-- 4. ASSIGNMENT ANALYTICS
-- Grain: one row per assignment
-- ============================================================

DROP VIEW IF EXISTS vw_assignment_analytics;

CREATE VIEW vw_assignment_analytics AS
SELECT

    a.assignment_id,
    a.assignment_title,
    a.assignment_type,
    a.difficulty_level,
    a.expected_word_count,
    a.max_word_count,

    a.prompt_complexity,
    a.open_endedness,
    a.research_intensity,
    a.rubric_specificity,

    a.requires_citations,
    a.required_references,
    a.research_required,
    a.oral_defense_required,
    a.collaboration_allowed,
    a.allowed_ai_usage,
    a.design_type,

    a.assignment_open_at,
    a.submission_deadline,

    o.offering_id,
    o.section_code,
    o.class_size,
    o.delivery_mode,

    c.course_id,
    c.course_code,
    c.course_name,
    c.subject_area,
    c.course_level,
    c.difficulty_level AS course_difficulty,
    c.credits,

    t.term_id,
    t.term_name,
    t.academic_year,
    t.term_type,

    i.instructor_id,
    i.instructor_name,
    i.academic_rank,
    i.years_experience,
    i.teaching_load,
    i.ai_policy_adoption,

    dept.department_id,
    dept.department_name,

    COUNT(s.submission_id)
        AS total_submissions,

    SUM(
        CASE
            WHEN s.is_ai_generated = 1
            THEN 1
            ELSE 0
        END
    ) AS ai_generated_submissions,

    AVG(s.word_count)
        AS avg_word_count,

    AVG(s.similarity_score)
        AS avg_similarity_score,

    AVG(s.time_spent_minutes)
        AS avg_time_spent_minutes,

    AVG(s.editing_sessions)
        AS avg_editing_sessions,

    AVG(s.copy_paste_ratio)
        AS avg_copy_paste_ratio,

    AVG(s.perplexity_score)
        AS avg_perplexity_score,

    AVG(s.burstiness_score)
        AS avg_burstiness_score,

    AVG(s.semantic_coherence)
        AS avg_semantic_coherence,

    AVG(s.grade)
        AS avg_grade

FROM assignments a

LEFT JOIN course_offerings o
    ON a.offering_id = o.offering_id

LEFT JOIN courses c
    ON o.course_id = c.course_id

LEFT JOIN academic_terms t
    ON o.term_id = t.term_id

LEFT JOIN instructors i
    ON o.instructor_id = i.instructor_id

LEFT JOIN departments dept
    ON c.department_id = dept.department_id

LEFT JOIN submissions s
    ON a.assignment_id = s.assignment_id

GROUP BY

    a.assignment_id,
    a.assignment_title,
    a.assignment_type,
    a.difficulty_level,
    a.expected_word_count,
    a.max_word_count,

    a.prompt_complexity,
    a.open_endedness,
    a.research_intensity,
    a.rubric_specificity,

    a.requires_citations,
    a.required_references,
    a.research_required,
    a.oral_defense_required,
    a.collaboration_allowed,
    a.allowed_ai_usage,
    a.design_type,

    a.assignment_open_at,
    a.submission_deadline,

    o.offering_id,
    o.section_code,
    o.class_size,
    o.delivery_mode,

    c.course_id,
    c.course_code,
    c.course_name,
    c.subject_area,
    c.course_level,
    c.difficulty_level,
    c.credits,

    t.term_id,
    t.term_name,
    t.academic_year,
    t.term_type,

    i.instructor_id,
    i.instructor_name,
    i.academic_rank,
    i.years_experience,
    i.teaching_load,
    i.ai_policy_adoption,

    dept.department_id,
    dept.department_name;


-- ============================================================
-- 5. INTEGRITY CASE ANALYSIS
-- Grain: one row per integrity case
-- ============================================================

DROP VIEW IF EXISTS vw_integrity_case_analysis;

CREATE VIEW vw_integrity_case_analysis AS
SELECT

    ic.case_id,
    ic.student_id,
    CONCAT(
        st.first_name,
        ' ',
        st.last_name
    ) AS student_name,

    st.year_level,
    st.gpa,
    st.academic_standing,

    m.major_name,
    dept.department_name,

    ic.submission_id,
    ic.assignment_id,

    a.assignment_title,
    a.assignment_type,

    c.course_code,
    c.course_name,
    c.subject_area,

    t.term_name,
    t.academic_year,

    i.instructor_name,

    ic.case_open_date,
    ic.incident_date,

    ic.case_type,
    ic.trigger_source,
    ic.initial_suspicion_level,
    ic.evidence_strength,

    ic.plagiarism_flag,
    ic.ai_detector_flag,
    ic.network_flag,
    ic.faculty_report,

    ic.investigation_duration_days,
    ic.student_response,
    ic.appealed,
    ic.appeal_date,

    ic.verdict,
    ic.sanction_level,
    ic.sanction_type,
    ic.sanction_points,
    ic.case_closed_date,

    CASE
        WHEN ic.case_open_date IS NOT NULL
         AND ic.case_closed_date IS NOT NULL
        THEN
            DATEDIFF(
                ic.case_closed_date,
                ic.case_open_date
            )
        ELSE NULL
    END AS case_duration_days

FROM integrity_cases ic

LEFT JOIN students st
    ON ic.student_id = st.student_id

LEFT JOIN majors m
    ON st.major_id = m.major_id

LEFT JOIN departments dept
    ON m.department_id = dept.department_id

LEFT JOIN submissions s
    ON ic.submission_id = s.submission_id

LEFT JOIN assignments a
    ON ic.assignment_id = a.assignment_id

LEFT JOIN course_offerings o
    ON a.offering_id = o.offering_id

LEFT JOIN courses c
    ON o.course_id = c.course_id

LEFT JOIN academic_terms t
    ON o.term_id = t.term_id

LEFT JOIN instructors i
    ON o.instructor_id = i.instructor_id;


-- ============================================================
-- 6. BEHAVIOR EVENT ANALYSIS
-- Grain: one row per behavior event
-- ============================================================

DROP VIEW IF EXISTS vw_behavior_event_analysis;

CREATE VIEW vw_behavior_event_analysis AS
SELECT

    e.event_id,
    e.student_id,

    CONCAT(
        st.first_name,
        ' ',
        st.last_name
    ) AS student_name,

    st.year_level,
    st.gpa,

    m.major_name,
    dept.department_name,

    e.event_date,
    e.event_type,
    e.severity,

    e.course_id,
    c.course_code,
    c.course_name,
    c.subject_area,

    e.related_submission_id,

    a.assignment_id,
    a.assignment_title,
    a.assignment_type,

    e.event_value,
    e.description_code,
    e.resolved

FROM student_behavior_events e

LEFT JOIN students st
    ON e.student_id = st.student_id

LEFT JOIN majors m
    ON st.major_id = m.major_id

LEFT JOIN departments dept
    ON m.department_id = dept.department_id

LEFT JOIN courses c
    ON e.course_id = c.course_id

LEFT JOIN submissions s
    ON e.related_submission_id = s.submission_id

LEFT JOIN assignments a
    ON s.assignment_id = a.assignment_id;


-- ============================================================
-- 7. VIEW QA
-- ============================================================

-- Primary grain checks
SELECT
    'vw_submission_analytics' AS view_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT submission_id) AS distinct_key_count
FROM vw_submission_analytics

UNION ALL

SELECT
    'vw_detector_analysis',
    COUNT(*),
    COUNT(DISTINCT detector_result_id)
FROM vw_detector_analysis

UNION ALL

SELECT
    'vw_student_integrity_profile',
    COUNT(*),
    COUNT(DISTINCT student_id)
FROM vw_student_integrity_profile

UNION ALL

SELECT
    'vw_assignment_analytics',
    COUNT(*),
    COUNT(DISTINCT assignment_id)
FROM vw_assignment_analytics

UNION ALL

SELECT
    'vw_integrity_case_analysis',
    COUNT(*),
    COUNT(DISTINCT case_id)
FROM vw_integrity_case_analysis

UNION ALL

SELECT
    'vw_behavior_event_analysis',
    COUNT(*),
    COUNT(DISTINCT event_id)
FROM vw_behavior_event_analysis;


-- ============================================================
-- 8. POWER BI QUICK CHECKS
-- ============================================================

SELECT
    COUNT(*) AS submissions,
    SUM(is_ai_generated) AS ai_generated,
    ROUND(
        AVG(is_ai_generated) * 100,
        2
    ) AS ai_generated_percentage,
    ROUND(
        AVG(mean_detector_ai_probability) * 100,
        2
    ) AS average_detector_probability,
    ROUND(
        AVG(similarity_score) * 100,
        2
    ) AS average_similarity_percentage
FROM vw_submission_analytics;

SELECT
    department_name,
    COUNT(*) AS submissions,
    SUM(is_ai_generated) AS ai_generated_submissions,
    ROUND(
        AVG(is_ai_generated) * 100,
        2
    ) AS ai_generated_rate
FROM vw_submission_analytics
GROUP BY department_name
ORDER BY ai_generated_rate DESC;

SELECT
    tool_name,
    COUNT(*) AS detector_runs,
    ROUND(
        AVG(ai_probability) * 100,
        2
    ) AS avg_ai_probability,
    ROUND(
        AVG(confidence_score) * 100,
        2
    ) AS avg_confidence,
    SUM(
        CASE
            WHEN detected_as_ai = 1 THEN 1
            ELSE 0
        END
    ) AS ai_flags
FROM vw_detector_analysis
GROUP BY tool_name
ORDER BY avg_ai_probability DESC;

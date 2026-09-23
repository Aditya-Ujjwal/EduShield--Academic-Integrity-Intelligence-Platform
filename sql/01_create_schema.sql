-- ============================================================
-- EduShield
-- 01_create_schema.sql
-- ============================================================
-- Creates the MySQL database and the 14 cleaned relational tables.
-- Foreign keys are added after data loading by 02_add_constraints.sql
-- so the initial load is easier to diagnose.
-- ============================================================

CREATE DATABASE IF NOT EXISTS edushield
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE edushield;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS student_integrity_history;
DROP TABLE IF EXISTS integrity_cases;
DROP TABLE IF EXISTS student_behavior_events;
DROP TABLE IF EXISTS ai_detector_results;
DROP TABLE IF EXISTS detector_tools;
DROP TABLE IF EXISTS submissions;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS course_offerings;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS instructors;
DROP TABLE IF EXISTS majors;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS academic_terms;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- 1. ACADEMIC TERMS
-- ============================================================

CREATE TABLE academic_terms (
    term_id VARCHAR(20) NOT NULL,
    term_name VARCHAR(50) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    term_type VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    PRIMARY KEY (term_id),
    INDEX idx_terms_dates (start_date, end_date)
) ENGINE=InnoDB;

-- ============================================================
-- 2. DEPARTMENTS
-- ============================================================

CREATE TABLE departments (
    department_id VARCHAR(20) NOT NULL,
    department_name VARCHAR(100) NOT NULL,
    department_code VARCHAR(20) NOT NULL,

    PRIMARY KEY (department_id),
    UNIQUE KEY uq_department_code (department_code)
) ENGINE=InnoDB;

-- ============================================================
-- 3. MAJORS
-- ============================================================

CREATE TABLE majors (
    major_id VARCHAR(20) NOT NULL,
    major_name VARCHAR(100) NOT NULL,
    department_id VARCHAR(20) NOT NULL,

    PRIMARY KEY (major_id),
    INDEX idx_majors_department (department_id)
) ENGINE=InnoDB;

-- ============================================================
-- 4. INSTRUCTORS
-- ============================================================

CREATE TABLE instructors (
    instructor_id VARCHAR(20) NOT NULL,
    instructor_name VARCHAR(120) NOT NULL,
    department_id VARCHAR(20) NOT NULL,
    academic_rank VARCHAR(50),
    years_experience DECIMAL(5,1),
    teaching_load INT,
    ai_policy_adoption VARCHAR(30),

    PRIMARY KEY (instructor_id),
    INDEX idx_instructors_department (department_id)
) ENGINE=InnoDB;

-- ============================================================
-- 5. STUDENTS
-- ============================================================

CREATE TABLE students (
    student_id VARCHAR(20) NOT NULL,
    first_name VARCHAR(60),
    last_name VARCHAR(60),
    gender VARCHAR(30),
    year_level VARCHAR(30),
    major_id VARCHAR(20),
    gpa DECIMAL(4,2),
    enrollment_date DATE,
    expected_graduation_year INT,
    attendance_rate DECIMAL(6,2),
    academic_standing VARCHAR(50),
    scholarship_status VARCHAR(40),
    active_status VARCHAR(30),

    PRIMARY KEY (student_id),
    INDEX idx_students_major (major_id)
) ENGINE=InnoDB;

-- ============================================================
-- 6. COURSES
-- ============================================================

CREATE TABLE courses (
    course_id VARCHAR(20) NOT NULL,
    course_code VARCHAR(30) NOT NULL,
    course_name VARCHAR(150) NOT NULL,
    department_id VARCHAR(20) NOT NULL,
    subject_area VARCHAR(100),
    course_level VARCHAR(30),
    difficulty_level VARCHAR(30),
    credits INT,

    PRIMARY KEY (course_id),
    UNIQUE KEY uq_course_code (course_code),
    INDEX idx_courses_department (department_id)
) ENGINE=InnoDB;

-- ============================================================
-- 7. COURSE OFFERINGS
-- ============================================================

CREATE TABLE course_offerings (
    offering_id VARCHAR(20) NOT NULL,
    course_id VARCHAR(20) NOT NULL,
    term_id VARCHAR(20) NOT NULL,
    instructor_id VARCHAR(20) NOT NULL,
    section_code VARCHAR(30),
    room_code VARCHAR(30),
    class_size INT,
    delivery_mode VARCHAR(40),

    PRIMARY KEY (offering_id),
    INDEX idx_offerings_course (course_id),
    INDEX idx_offerings_term (term_id),
    INDEX idx_offerings_instructor (instructor_id)
) ENGINE=InnoDB;

-- ============================================================
-- 8. ASSIGNMENTS
-- ============================================================

CREATE TABLE assignments (
    assignment_id VARCHAR(30) NOT NULL,
    offering_id VARCHAR(20) NOT NULL,
    assignment_title VARCHAR(255),
    assignment_type VARCHAR(50),
    difficulty_level VARCHAR(30),
    expected_word_count INT,
    max_word_count INT,

    prompt_complexity DECIMAL(7,2),
    open_endedness DECIMAL(7,2),
    research_intensity DECIMAL(7,2),
    rubric_specificity DECIMAL(7,2),

    requires_citations BOOLEAN,
    required_references INT,
    research_required BOOLEAN,
    oral_defense_required BOOLEAN,
    collaboration_allowed BOOLEAN,

    allowed_ai_usage VARCHAR(40),
    design_type VARCHAR(50),

    assignment_open_at DATETIME,
    submission_deadline DATETIME,

    PRIMARY KEY (assignment_id),
    INDEX idx_assignments_offering (offering_id),
    INDEX idx_assignments_deadline (submission_deadline)
) ENGINE=InnoDB;

-- ============================================================
-- 9. SUBMISSIONS
-- ============================================================

CREATE TABLE submissions (
    submission_id VARCHAR(30) NOT NULL,
    student_id VARCHAR(20) NOT NULL,
    assignment_id VARCHAR(30) NOT NULL,
    submitted_at DATETIME,
    submission_status VARCHAR(30),

    word_count INT,
    cited_references INT,
    similarity_score DECIMAL(8,5),
    late_submission BOOLEAN,
    hours_before_deadline DECIMAL(10,2),

    editing_sessions INT,
    revision_count INT,
    draft_count INT,
    time_spent_minutes INT,
    copy_paste_ratio DECIMAL(8,5),
    number_of_edits INT,

    typing_consistency DECIMAL(8,5),
    avg_sentence_length DECIMAL(8,3),
    sentence_length_std DECIMAL(8,3),
    vocabulary_richness DECIMAL(8,5),
    lexical_diversity DECIMAL(8,5),
    repetition_ratio DECIMAL(8,5),
    paragraph_count INT,
    grammar_error_rate DECIMAL(8,5),
    citation_density DECIMAL(8,5),
    semantic_coherence DECIMAL(8,5),
    perplexity_score DECIMAL(8,5),
    burstiness_score DECIMAL(8,5),

    grade DECIMAL(6,2),
    feedback_score DECIMAL(6,2),

    is_ai_generated BOOLEAN,
    ai_generation_source VARCHAR(40),

    PRIMARY KEY (submission_id),
    INDEX idx_submissions_student (student_id),
    INDEX idx_submissions_assignment (assignment_id),
    INDEX idx_submissions_date (submitted_at),
    INDEX idx_submissions_target (is_ai_generated)
) ENGINE=InnoDB;

-- ============================================================
-- 10. DETECTOR TOOLS
-- ============================================================

CREATE TABLE detector_tools (
    tool_id VARCHAR(20) NOT NULL,
    tool_name VARCHAR(80) NOT NULL,
    vendor VARCHAR(120),
    model_version VARCHAR(60),
    baseline_false_positive_rate DECIMAL(8,5),
    baseline_false_negative_rate DECIMAL(8,5),
    calibration_score DECIMAL(8,5),
    active_status BOOLEAN,

    PRIMARY KEY (tool_id),
    UNIQUE KEY uq_detector_tool_name (tool_name)
) ENGINE=InnoDB;

-- ============================================================
-- 11. AI DETECTOR RESULTS
-- ============================================================

CREATE TABLE ai_detector_results (
    detector_result_id VARCHAR(30) NOT NULL,
    submission_id VARCHAR(30) NOT NULL,
    tool_id VARCHAR(20) NOT NULL,
    test_timestamp DATETIME,

    ai_probability DECIMAL(8,5),
    confidence_score DECIMAL(8,5),
    detected_as_ai BOOLEAN,
    writing_style_score DECIMAL(8,5),
    detector_perplexity_score DECIMAL(8,5),
    text_length INT,
    processing_status VARCHAR(30),

    PRIMARY KEY (detector_result_id),
    INDEX idx_detector_results_submission (submission_id),
    INDEX idx_detector_results_tool (tool_id),
    INDEX idx_detector_results_timestamp (test_timestamp),
    INDEX idx_detector_results_ai_flag (detected_as_ai)
) ENGINE=InnoDB;

-- ============================================================
-- 12. STUDENT BEHAVIOR EVENTS
-- ============================================================

CREATE TABLE student_behavior_events (
    event_id BIGINT NOT NULL,
    student_id VARCHAR(20) NOT NULL,
    event_date DATETIME,
    event_type VARCHAR(60),
    severity VARCHAR(20),
    course_id VARCHAR(20),
    related_submission_id VARCHAR(30),
    event_value DECIMAL(12,4),
    description_code VARCHAR(80),
    resolved BOOLEAN,

    PRIMARY KEY (event_id),
    INDEX idx_behavior_student (student_id),
    INDEX idx_behavior_date (event_date),
    INDEX idx_behavior_course (course_id),
    INDEX idx_behavior_submission (related_submission_id)
) ENGINE=InnoDB;

-- ============================================================
-- 13. INTEGRITY CASES
-- ============================================================

CREATE TABLE integrity_cases (
    case_id VARCHAR(30) NOT NULL,
    student_id VARCHAR(20) NOT NULL,
    submission_id VARCHAR(30),
    assignment_id VARCHAR(30),

    case_open_date DATETIME,
    incident_date DATETIME,

    case_type VARCHAR(60),
    trigger_source VARCHAR(60),
    initial_suspicion_level VARCHAR(30),
    evidence_strength DECIMAL(8,5),

    plagiarism_flag BOOLEAN,
    ai_detector_flag BOOLEAN,
    network_flag BOOLEAN,
    faculty_report BOOLEAN,

    investigation_duration_days INT,
    student_response VARCHAR(120),
    appealed BOOLEAN,
    appeal_date DATETIME,

    verdict VARCHAR(40),
    sanction_level VARCHAR(40),
    sanction_type VARCHAR(60),
    sanction_points DECIMAL(8,2),

    case_closed_date DATETIME,

    PRIMARY KEY (case_id),
    INDEX idx_cases_student (student_id),
    INDEX idx_cases_submission (submission_id),
    INDEX idx_cases_assignment (assignment_id),
    INDEX idx_cases_incident (incident_date),
    INDEX idx_cases_verdict (verdict)
) ENGINE=InnoDB;

-- ============================================================
-- 14. STUDENT INTEGRITY HISTORY
-- ============================================================

CREATE TABLE student_integrity_history (
    history_id VARCHAR(30) NOT NULL,
    student_id VARCHAR(20) NOT NULL,
    snapshot_at DATETIME,

    integrity_score DECIMAL(8,5),
    trust_factor_score DECIMAL(8,5),

    prior_confirmed_cases INT,
    prior_dismissed_cases INT,
    prior_suspicious_flags INT,
    prior_ai_flags INT,
    prior_plagiarism_flags INT,
    prior_sanction_points DECIMAL(8,2),
    recent_integrity_events INT,

    integrity_status VARCHAR(40),

    PRIMARY KEY (history_id),
    INDEX idx_history_student (student_id),
    INDEX idx_history_snapshot (snapshot_at)
) ENGINE=InnoDB;

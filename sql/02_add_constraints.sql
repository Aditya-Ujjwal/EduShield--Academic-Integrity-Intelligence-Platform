-- ============================================================
-- EduShield
-- 02_add_constraints.sql
-- ============================================================

USE edushield;

SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE majors
    ADD CONSTRAINT fk_majors_department
    FOREIGN KEY (department_id)
    REFERENCES departments(department_id);

ALTER TABLE instructors
    ADD CONSTRAINT fk_instructors_department
    FOREIGN KEY (department_id)
    REFERENCES departments(department_id);

ALTER TABLE students
    ADD CONSTRAINT fk_students_major
    FOREIGN KEY (major_id)
    REFERENCES majors(major_id);

ALTER TABLE courses
    ADD CONSTRAINT fk_courses_department
    FOREIGN KEY (department_id)
    REFERENCES departments(department_id);

ALTER TABLE course_offerings
    ADD CONSTRAINT fk_offerings_course
    FOREIGN KEY (course_id)
    REFERENCES courses(course_id),
    ADD CONSTRAINT fk_offerings_term
    FOREIGN KEY (term_id)
    REFERENCES academic_terms(term_id),
    ADD CONSTRAINT fk_offerings_instructor
    FOREIGN KEY (instructor_id)
    REFERENCES instructors(instructor_id);

ALTER TABLE assignments
    ADD CONSTRAINT fk_assignments_offering
    FOREIGN KEY (offering_id)
    REFERENCES course_offerings(offering_id);

ALTER TABLE submissions
    ADD CONSTRAINT fk_submissions_student
    FOREIGN KEY (student_id)
    REFERENCES students(student_id),
    ADD CONSTRAINT fk_submissions_assignment
    FOREIGN KEY (assignment_id)
    REFERENCES assignments(assignment_id);

ALTER TABLE ai_detector_results
    ADD CONSTRAINT fk_detector_results_submission
    FOREIGN KEY (submission_id)
    REFERENCES submissions(submission_id),
    ADD CONSTRAINT fk_detector_results_tool
    FOREIGN KEY (tool_id)
    REFERENCES detector_tools(tool_id);

ALTER TABLE student_behavior_events
    ADD CONSTRAINT fk_behavior_student
    FOREIGN KEY (student_id)
    REFERENCES students(student_id),
    ADD CONSTRAINT fk_behavior_course
    FOREIGN KEY (course_id)
    REFERENCES courses(course_id),
    ADD CONSTRAINT fk_behavior_submission
    FOREIGN KEY (related_submission_id)
    REFERENCES submissions(submission_id);

ALTER TABLE integrity_cases
    ADD CONSTRAINT fk_cases_student
    FOREIGN KEY (student_id)
    REFERENCES students(student_id),
    ADD CONSTRAINT fk_cases_submission
    FOREIGN KEY (submission_id)
    REFERENCES submissions(submission_id),
    ADD CONSTRAINT fk_cases_assignment
    FOREIGN KEY (assignment_id)
    REFERENCES assignments(assignment_id);

ALTER TABLE student_integrity_history
    ADD CONSTRAINT fk_history_student
    FOREIGN KEY (student_id)
    REFERENCES students(student_id);

SET FOREIGN_KEY_CHECKS = 1;

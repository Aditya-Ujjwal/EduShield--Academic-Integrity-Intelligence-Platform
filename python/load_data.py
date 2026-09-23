"""
EduShield — Python CSV → MySQL Loader

The loader reads the cleaned CSVs from data/processed and inserts them
into the pre-created MySQL schema.

Credentials are read from .env:
    MYSQL_HOST
    MYSQL_PORT
    MYSQL_USER
    MYSQL_PASSWORD
    MYSQL_DATABASE

Typical run from the EduShield project root:

    python python/load_data.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(PROJECT_ROOT / ".env")

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "edushield")


if not MYSQL_USER:
    raise RuntimeError(
        "MYSQL_USER is missing from .env"
    )


# ============================================================
# TABLE LOAD ORDER
# ============================================================

TABLE_FILES = [
    ("academic_terms", "academic_terms.csv"),
    ("departments", "departments.csv"),
    ("majors", "majors.csv"),
    ("instructors", "instructors.csv"),
    ("students", "students.csv"),
    ("courses", "courses.csv"),
    ("course_offerings", "course_offerings.csv"),
    ("assignments", "assignments.csv"),
    ("submissions", "submissions.csv"),
    ("detector_tools", "detector_tools.csv"),
    ("ai_detector_results", "ai_detector_results.csv"),
    ("student_behavior_events", "student_behavior_events.csv"),
    ("integrity_cases", "integrity_cases.csv"),
    ("student_integrity_history", "student_integrity_history.csv"),
]


# ============================================================
# COLUMN CONVERSION RULES
# ============================================================

DATETIME_COLUMNS = {
    "start_date",
    "end_date",
    "enrollment_date",
    "assignment_open_at",
    "submission_deadline",
    "submitted_at",
    "test_timestamp",
    "event_date",
    "case_open_date",
    "incident_date",
    "appeal_date",
    "case_closed_date",
    "snapshot_at",
}

# Boolean columns are table-specific because the same column name
# can have different meanings/types across the relational model.
#
# Example:
# - detector_tools.active_status = TRUE/FALSE
# - students.active_status = "Active"/"Inactive"
TABLE_BOOLEAN_COLUMNS = {
    "assignments": {
        "requires_citations",
        "research_required",
        "oral_defense_required",
        "collaboration_allowed",
    },
    "submissions": {
        "late_submission",
        "is_ai_generated",
    },
    "detector_tools": {
        "active_status",
    },
    "ai_detector_results": {
        "detected_as_ai",
    },
    "student_behavior_events": {
        "resolved",
    },
    "integrity_cases": {
        "plagiarism_flag",
        "ai_detector_flag",
        "network_flag",
        "faculty_report",
        "appealed",
    },
}

INTEGER_COLUMNS = {
    "expected_word_count",
    "max_word_count",
    "required_references",
    "word_count",
    "cited_references",
    "editing_sessions",
    "revision_count",
    "draft_count",
    "time_spent_minutes",
    "number_of_edits",
    "paragraph_count",
    "text_length",
    "class_size",
    "teaching_load",
    "credits",
    "expected_graduation_year",
    "investigation_duration_days",
    "prior_confirmed_cases",
    "prior_dismissed_cases",
    "prior_suspicious_flags",
    "prior_ai_flags",
    "prior_plagiarism_flags",
    "recent_integrity_events",
}

NUMERIC_COLUMNS = {
    "years_experience",
    "gpa",
    "attendance_rate",
    "prompt_complexity",
    "open_endedness",
    "research_intensity",
    "rubric_specificity",
    "similarity_score",
    "hours_before_deadline",
    "copy_paste_ratio",
    "typing_consistency",
    "avg_sentence_length",
    "sentence_length_std",
    "vocabulary_richness",
    "lexical_diversity",
    "repetition_ratio",
    "grammar_error_rate",
    "citation_density",
    "semantic_coherence",
    "perplexity_score",
    "burstiness_score",
    "ai_probability",
    "confidence_score",
    "writing_style_score",
    "detector_perplexity_score",
    "event_value",
    "evidence_strength",
    "sanction_points",
    "prior_sanction_points",
    "integrity_score",
    "trust_factor_score",
    "baseline_false_positive_rate",
    "baseline_false_negative_rate",
    "calibration_score",
    "grade",
    "feedback_score",
}

# The loader uses this variable inside clean_dataframe() so that
# only booleans belonging to the current table are normalized.
CURRENT_TABLE_NAME = None

# ============================================================
# ENGINE
# ============================================================

DATABASE_URL = (
    f"mysql+pymysql://"
    f"{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    "?charset=utf8mb4"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)


# ============================================================
# HELPERS
# ============================================================

def normalize_bool(value):
    if pd.isna(value):
        return None

    if isinstance(value, (bool, np.bool_)):
        return bool(value)

    text_value = (
        str(value)
        .strip()
        .lower()
    )

    mapping = {
        "true": True,
        "false": False,
        "yes": True,
        "no": False,
        "1": True,
        "0": False,
        "y": True,
        "n": False,
    }

    if text_value in mapping:
        return mapping[text_value]

    raise ValueError(
        f"Unexpected boolean value: {value!r}"
    )


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize the cleaned CSV for MySQL insertion."""
    df = df.copy()

    # Preserve legitimate string "None"; only blank CSV cells become NULL.
    df = df.replace(
        {
            np.nan: None,
            pd.NA: None,
            pd.NaT: None,
        }
    )

    for column in DATETIME_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
            )

    boolean_columns = TABLE_BOOLEAN_COLUMNS.get(
        CURRENT_TABLE_NAME,
        set(),
    )

    for column in boolean_columns:
        if column in df.columns:
            df[column] = df[column].apply(
                normalize_bool
            )

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    # Keep counts integer where present, while allowing NULLs.
    for column in INTEGER_COLUMNS:
        if column in df.columns:
            converted = pd.to_numeric(
                df[column],
                errors="coerce",
            )

            # MySQL INT accepts Python ints or None.
            df[column] = converted.apply(
                lambda value:
                    None
                    if pd.isna(value)
                    else int(round(float(value)))
            )

    # Convert pandas missing values to Python None after all coercion.
    df = df.astype(object).where(
        pd.notna(df),
        None,
    )

    return df


def get_table_count(table_name: str) -> int:
    with engine.connect() as connection:
        return int(
            connection.execute(
                text(
                    f"SELECT COUNT(*) FROM `{table_name}`"
                )
            ).scalar_one()
        )


def load_table(
    table_name: str,
    filename: str,
    chunksize: int = 1000,
) -> int:
    """Load one processed CSV into its MySQL table."""
    path = PROCESSED_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Processed CSV not found: {path}"
        )

    print(
        f"\nLoading {table_name}..."
    )

    df = pd.read_csv(
        path,
        low_memory=False,
        keep_default_na=False,
        na_values=[""],
    )

    print(
        f"  CSV rows: {len(df):,}"
    )

    expected_boolean_columns = TABLE_BOOLEAN_COLUMNS.get(
        table_name,
        set(),
    )

    # Do not silently convert unexpected categorical values.
    missing_boolean_columns = (
        expected_boolean_columns
        - set(df.columns)
    )

    if missing_boolean_columns:
        raise RuntimeError(
            f"{table_name}: expected boolean columns missing: "
            f"{sorted(missing_boolean_columns)}"
        )

    global CURRENT_TABLE_NAME
    CURRENT_TABLE_NAME = table_name

    df = clean_dataframe(df)

    # Clear the table before loading so the script is repeatable.
    with engine.begin() as connection:
        connection.execute(
            text(
                f"DELETE FROM `{table_name}`"
            )
        )

    inserted = 0

    df.to_sql(
        table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=chunksize,
        method="multi",
    )

    inserted = len(df)

    db_count = get_table_count(
        table_name
    )

    print(
        f"  Inserted: {inserted:,}"
    )

    print(
        f"  DB rows:  {db_count:,}"
    )

    if db_count != inserted:
        raise RuntimeError(
            f"Row-count mismatch for {table_name}: "
            f"expected {inserted}, got {db_count}"
        )

    CURRENT_TABLE_NAME = None

    return inserted


# ============================================================
# POST-LOAD VALIDATION
# ============================================================

def run_basic_validation():
    print(
        "\n" + "=" * 70
    )
    print(
        "POST-LOAD VALIDATION"
    )
    print(
        "=" * 70
    )

    with engine.connect() as connection:
        checks = [
            (
                "submissions with invalid student",
                """
                SELECT COUNT(*)
                FROM submissions s
                LEFT JOIN students st
                    ON s.student_id = st.student_id
                WHERE st.student_id IS NULL
                """,
            ),
            (
                "submissions with invalid assignment",
                """
                SELECT COUNT(*)
                FROM submissions s
                LEFT JOIN assignments a
                    ON s.assignment_id = a.assignment_id
                WHERE a.assignment_id IS NULL
                """,
            ),
            (
                "detector results with invalid submission",
                """
                SELECT COUNT(*)
                FROM ai_detector_results d
                LEFT JOIN submissions s
                    ON d.submission_id = s.submission_id
                WHERE s.submission_id IS NULL
                """,
            ),
            (
                "detector results with invalid tool",
                """
                SELECT COUNT(*)
                FROM ai_detector_results d
                LEFT JOIN detector_tools t
                    ON d.tool_id = t.tool_id
                WHERE t.tool_id IS NULL
                """,
            ),
            (
                "history with invalid student",
                """
                SELECT COUNT(*)
                FROM student_integrity_history h
                LEFT JOIN students s
                    ON h.student_id = s.student_id
                WHERE s.student_id IS NULL
                """,
            ),
        ]

        for label, query in checks:
            value = int(
                connection.execute(
                    text(query)
                ).scalar_one()
            )

            print(
                f"{label}: {value}"
            )

            if value != 0:
                raise RuntimeError(
                    f"Validation failed: {label}"
                )

        target_rows = connection.execute(
            text(
                """
                SELECT
                    is_ai_generated,
                    COUNT(*) AS submission_count
                FROM submissions
                GROUP BY is_ai_generated
                ORDER BY is_ai_generated
                """
            )
        ).fetchall()

        print(
            "\nTarget distribution:"
        )

        for row in target_rows:
            print(
                f"  {row[0]} -> {row[1]:,}"
            )


# ============================================================
# MAIN
# ============================================================

def main():
    print(
        "=" * 70
    )
    print(
        "EduShield CSV → MySQL Loader"
    )
    print(
        "=" * 70
    )

    print(
        f"Project root:  {PROJECT_ROOT}"
    )

    print(
        f"Processed dir: {PROCESSED_DIR}"
    )

    print(
        f"Database:      {MYSQL_DATABASE}"
    )

    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

        print(
            "\nMySQL connection: OK"
        )

        total_rows = 0

        for table_name, filename in TABLE_FILES:
            total_rows += load_table(
                table_name,
                filename,
            )

        run_basic_validation()

        print(
            "\n" + "=" * 70
        )
        print(
            "LOAD COMPLETED SUCCESSFULLY"
        )
        print(
            f"Total rows inserted: {total_rows:,}"
        )
        print(
            "=" * 70
        )

        print(
            "\nNext step:"
        )
        print(
            "Run sql/02_add_constraints.sql in MySQL Workbench."
        )

    except (SQLAlchemyError, OSError, ValueError, RuntimeError) as exc:
        print(
            "\nLOAD FAILED"
        )
        print(
            str(exc)
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

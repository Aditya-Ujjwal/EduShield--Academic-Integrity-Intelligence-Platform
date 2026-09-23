"""
EduShield — AI Submission Screening

Interactive machine-learning screening interface for a newly submitted
academic assignment. It combines an existing student profile, assignment
context, submission behavior, historical signals, and multiple AI-detector
outputs.

The underlying project dataset is synthetic and intended for portfolio/demo
use. The prediction is a screening indicator, not an automated disciplinary
verdict.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="EduShield | AI Submission Screening",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    :root {
        --ed-bg: #07111f !important;
        --ed-surface: #0d1a2b !important;
        --ed-surface-2: #102239 !important;
        --ed-border: #213653 !important;
        --ed-text: #f8fafc !important;
        --ed-muted: #94a3b8 !important;
        --ed-blue: #60a5fa !important;
        --ed-cyan: #22d3ee !important;
        --ed-green: #34d399 !important;
        --ed-amber: #fbbf24 !important;
        --ed-red: #fb7185 !important;
        --primary-color: #22d3ee !important;
    }

    html, body, .stApp, [class*="css"] {
        font-family: Inter, ui-sans-serif, system-ui, -apple-system,
                     BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        color: #f8fafc !important;
    }

    .stApp,
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(
                circle at 5% 0%,
                rgba(34, 211, 238, 0.10),
                transparent 27%
            ),
            radial-gradient(
                circle at 92% 5%,
                rgba(96, 165, 250, 0.10),
                transparent 25%
            ),
            linear-gradient(
                180deg,
                #07111f 0%,
                #091525 52%,
                #06101d 100%
            ) !important;
        --primary-color: #22d3ee !important;
    }

    [data-testid="stHeader"] {
        background: rgba(7, 17, 31, 0.78) !important;
    }

    .block-container {
        max-width: 1480px !important;
        padding-top: 1.45rem !important;
        padding-bottom: 3rem !important;
    }

    /* ---------------- Sidebar ---------------- */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #081323 0%,
                #0a1627 100%
            ) !important;
        border-right: 1px solid #1c3049 !important;
    }

    section[data-testid="stSidebar"] * {
        color: #dbe7f3 !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: #203651 !important;
    }

    /* ---------------- Global text ---------------- */

    h1, h2, h3, h4, h5, h6,
    p, span, label, small, li {
        color: #f8fafc !important;
    }

    [data-testid="stCaptionContainer"] * {
        color: #94a3b8 !important;
    }

    /* ---------------- Hero ---------------- */

    .hero {
        position: relative;
        overflow: hidden;
        padding: 1.75rem 2rem;
        border: 1px solid #29415f;
        border-radius: 24px;
        background:
            linear-gradient(
                120deg,
                rgba(15, 29, 49, 0.98) 0%,
                rgba(13, 35, 57, 0.96) 52%,
                rgba(23, 47, 82, 0.97) 100%
            );
        box-shadow:
            0 24px 70px rgba(0, 0, 0, 0.32),
            inset 0 1px 0 rgba(255,255,255,0.04);
        margin-bottom: 0.95rem;
    }

    .hero::after {
        content: "";
        position: absolute;
        width: 240px;
        height: 240px;
        right: -80px;
        top: -100px;
        border-radius: 50%;
        background: rgba(34, 211, 238, 0.11);
        filter: blur(3px);
    }

    .hero-kicker {
        color: #67e8f9 !important;
        font-size: 0.70rem;
        font-weight: 900;
        letter-spacing: 0.17em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }

    .hero-title {
        color: #f8fafc !important;
        font-size: 2.30rem;
        line-height: 1.08;
        font-weight: 900;
        margin: 0;
    }

    .hero-subtitle {
        color: #b9c8da !important;
        font-size: 0.93rem;
        margin-top: 0.65rem;
        max-width: 930px;
        line-height: 1.62;
    }

    .model-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.42rem 0.72rem;
        margin-top: 1rem;
        border: 1px solid rgba(52, 211, 153, 0.30);
        border-radius: 999px;
        background: rgba(52, 211, 153, 0.08);
        color: #86efac !important;
        font-size: 0.70rem;
        font-weight: 850;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .model-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #34d399;
        box-shadow: 0 0 14px rgba(52, 211, 153, 0.85);
    }

    /* ---------------- Workflow strip ---------------- */

    .workflow {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.60rem;
        margin-bottom: 1.25rem;
    }

    .workflow-item {
        padding: 0.78rem 0.88rem;
        border: 1px solid #203651;
        border-radius: 14px;
        background: rgba(13, 26, 43, 0.74);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.025);
    }

    .workflow-num {
        display: inline-flex;
        width: 24px;
        height: 24px;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: rgba(34,211,238,0.11);
        color: #67e8f9 !important;
        font-size: 0.70rem;
        font-weight: 900;
        margin-right: 0.48rem;
    }

    .workflow-title {
        color: #e2e8f0 !important;
        font-size: 0.77rem;
        font-weight: 850;
    }

    .workflow-sub {
        color: #71839a !important;
        display: block;
        margin-top: 0.26rem;
        padding-left: 2rem;
        font-size: 0.68rem;
    }

    /* ---------------- Banners ---------------- */

    .info-banner {
        background: rgba(30, 64, 175, 0.14);
        border: 1px solid rgba(96, 165, 250, 0.26);
        color: #bfdbfe !important;
        border-radius: 13px;
        padding: 0.76rem 0.92rem;
        font-size: 0.78rem;
        line-height: 1.52;
        margin: 0.5rem 0 1rem 0;
    }

    .warning-banner {
        background: rgba(180, 83, 9, 0.12);
        border: 1px solid rgba(251, 191, 36, 0.27);
        color: #fde68a !important;
        border-radius: 13px;
        padding: 0.76rem 0.92rem;
        font-size: 0.78rem;
        line-height: 1.52;
        margin: 0.5rem 0 1rem 0;
    }

    /* ---------------- Section headers ---------------- */

    .section-header {
        display: flex;
        align-items: center;
        gap: 0.76rem;
        margin: 1.45rem 0 0.78rem 0;
    }

    .section-number {
        display: inline-flex;
        width: 34px;
        height: 34px;
        flex: 0 0 34px;
        align-items: center;
        justify-content: center;
        border-radius: 11px;
        background: rgba(34,211,238,0.10);
        border: 1px solid rgba(34,211,238,0.23);
        color: #67e8f9 !important;
        font-size: 0.80rem;
        font-weight: 900;
    }

    .section-title {
        color: #f8fafc !important;
        font-size: 1.03rem;
        font-weight: 900;
        letter-spacing: -0.01em;
    }

    .section-subtitle {
        color: #71839a !important;
        font-size: 0.71rem;
        margin-top: 0.14rem;
    }

    /* ---------------- Cards / metrics ---------------- */

    .metric-card,
    .section-card {
        background:
            linear-gradient(
                180deg,
                rgba(15, 29, 48, 0.95),
                rgba(10, 23, 39, 0.95)
            ) !important;
        border: 1px solid #213653 !important;
        color: #f8fafc !important;
        border-radius: 16px;
        box-shadow:
            0 14px 36px rgba(0, 0, 0, 0.18),
            inset 0 1px 0 rgba(255,255,255,0.025);
    }

    .metric-card {
        padding: 0.90rem 0.98rem;
        min-height: 105px;
    }

    .metric-label {
        color: #71839a !important;
        font-size: 0.63rem;
        font-weight: 850;
        text-transform: uppercase;
        letter-spacing: 0.09em;
    }

    .metric-value {
        color: #f8fafc !important;
        font-size: 1.34rem;
        font-weight: 900;
        margin-top: 0.32rem;
    }

    .metric-caption {
        color: #71839a !important;
        font-size: 0.69rem;
        margin-top: 0.18rem;
    }

    .mini-label {
        color: #7dd3fc !important;
        font-size: 0.68rem;
        font-weight: 850;
        letter-spacing: 0.08em;
        margin-bottom: 0.15rem;
    }

    /* ---------------- Native widgets ---------------- */

    div[data-testid="stWidgetLabel"] *,
    div[data-testid="stWidgetLabel"] label,
    div[data-testid="stWidgetLabel"] p,
    div[data-testid="stWidgetLabel"] span {
        color: #dbe7f3 !important;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-testid="stTimeInput"] input,
    textarea {
        background: #0b1728 !important;
        color: #f8fafc !important;
        caret-color: #67e8f9 !important;
        border: 1px solid #2b4463 !important;
        border-radius: 10px !important;
    }

    div[data-testid="stNumberInput"] button {
        background: #132842 !important;
        color: #dbeafe !important;
        border-color: #29415f !important;
    }

    div[data-testid="stNumberInput"] button:hover {
        background: #183451 !important;
        color: #67e8f9 !important;
    }

    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus,
    div[data-testid="stDateInput"] input:focus,
    div[data-testid="stTimeInput"] input:focus {
        border-color: #22d3ee !important;
        box-shadow:
            0 0 0 1px rgba(34,211,238,0.20),
            inset 0 1px 2px rgba(0,0,0,0.20) !important;
    }

    div[data-baseweb="select"] > div {
        background: #0b1728 !important;
        color: #f8fafc !important;
        border: 1px solid #2b4463 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] * {
        color: #f8fafc !important;
    }

    ul[role="listbox"],
    div[role="listbox"] {
        background: #0b1728 !important;
        border: 1px solid #29415f !important;
    }

    ul[role="listbox"] li,
    div[role="option"] {
        color: #e2e8f0 !important;
        background: #0b1728 !important;
    }

    ul[role="listbox"] li:hover,
    div[role="option"]:hover {
        background: #132842 !important;
    }

    /* ---------------- Sliders ---------------- */

    div[data-testid="stSlider"] {
        --primary-color: #22d3ee !important;
    }

    div[data-testid="stSlider"] p,
    div[data-testid="stSlider"] label {
        color: #dbe7f3 !important;
    }

    div[data-testid="stSlider"] [role="slider"] {
        background: #22d3ee !important;
        border-color: #67e8f9 !important;
        box-shadow: 0 0 0 4px rgba(34,211,238,0.10) !important;
    }

    /* Streamlit's slider uses theme variables internally. */
    [data-baseweb="slider"] {
        --slider-color: #22d3ee !important;
        --primary-color: #22d3ee !important;
    }

    /* ---------------- Buttons ---------------- */

    .stButton > button,
    .stDownloadButton > button {
        min-height: 2.85rem;
        border-radius: 11px !important;
        font-weight: 850 !important;
        letter-spacing: 0.01em;
        border: 1px solid rgba(103, 232, 249, 0.22) !important;
        color: #07111f !important;
        background:
            linear-gradient(
                135deg,
                #67e8f9 0%,
                #22d3ee 100%
            ) !important;
        box-shadow:
            0 8px 24px rgba(34, 211, 238, 0.18);
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: #a5f3fc !important;
        transform: translateY(-1px);
        box-shadow:
            0 12px 30px rgba(34, 211, 238, 0.23);
    }

    /* ---------------- Expanders / dataframe ---------------- */

    div[data-testid="stMetric"] {
        background: #0d1a2b !important;
        border: 1px solid #213653 !important;
        border-radius: 14px !important;
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #f8fafc !important;
    }

    div[data-testid="stExpander"] {
        background: rgba(13, 26, 43, 0.76) !important;
        border: 1px solid #213653 !important;
        border-radius: 14px !important;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 14px !important;
        overflow: hidden !important;
        border: 1px solid #213653 !important;
    }

    /* ---------------- Result styling ---------------- */

    .result-title {
        color: #f8fafc !important;
        font-size: 1.75rem;
        font-weight: 900;
        margin-top: 0.35rem;
    }

    .screening-note {
        color: #94a3b8 !important;
        font-size: 0.75rem;
        line-height: 1.55;
        margin-top: 0.6rem;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.38rem 0.70rem;
        border-radius: 999px;
        font-weight: 850;
        font-size: 0.70rem;
        letter-spacing: 0.02em;
    }

    .pill-review {
        background: rgba(251,191,36,0.12);
        color: #fde68a !important;
        border: 1px solid rgba(251,191,36,0.20);
    }

    .pill-low {
        background: rgba(52,211,153,0.11);
        color: #86efac !important;
        border: 1px solid rgba(52,211,153,0.20);
    }

    .pill-high {
        background: rgba(251,113,133,0.11);
        color: #fda4af !important;
        border: 1px solid rgba(251,113,133,0.20);
    }

    .pill-neutral {
        background: rgba(148,163,184,0.10);
        color: #cbd5e1 !important;
        border: 1px solid rgba(148,163,184,0.18);
    }

    .js-plotly-plot,
    .plot-container,
    .svg-container {
        background: transparent !important;
    }

    footer {
        visibility: hidden !important;
    }

    @media (max-width: 900px) {
        .workflow {
            grid-template-columns: repeat(2, 1fr);
        }

        .hero-title {
            font-size: 1.85rem;
        }
    }

    @media (max-width: 600px) {
        .workflow {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ML_DIR = PROJECT_ROOT / "data" / "ml"
MODEL_DIR = PROJECT_ROOT / "models"

MODEL_PATH = MODEL_DIR / "edushield_ai_prediction_pipeline.joblib"
MANIFEST_PATH = MODEL_DIR / "feature_manifest.csv"
ML_DATA_PATH = ML_DIR / "edushield_submission_ml_data.parquet"


# ============================================================
# HELPERS
# ============================================================

def normalize_bool(value: Any) -> bool:
    """Normalize common boolean-like values."""
    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()

    mapping = {
        "true": True,
        "false": False,
        "yes": True,
        "no": False,
        "1": True,
        "0": False,
        "active": True,
        "inactive": False,
    }

    if text in mapping:
        return mapping[text]

    return False


def clean_id_series(series: pd.Series) -> pd.Series:
    """Normalize identifier values consistently with training."""
    return (
        series.astype("string")
        .str.strip()
        .str.upper()
    )


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert values to float while handling missing input."""
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Convert values to int while handling missing input."""
    try:
        if pd.isna(value):
            return default
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def prettify(value: Any) -> str:
    """Human-friendly formatting for categorical values."""
    text = str(value)
    return text.replace("_", " ").strip()


def load_csv(filename: str) -> pd.DataFrame:
    """Load a processed table."""
    path = PROCESSED_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required processed file was not found: {path}"
        )

    return pd.read_csv(
        path,
        low_memory=False,
        keep_default_na=False,
        na_values=[""],
    )


def build_assignment_context(
    assignments: pd.DataFrame,
    offerings: pd.DataFrame,
    courses: pd.DataFrame,
    instructors: pd.DataFrame,
    terms: pd.DataFrame,
    departments: pd.DataFrame,
) -> pd.DataFrame:
    """Recreate the same assignment/course/instructor/term context chain."""
    result = assignments.copy()

    key_columns = {
        "assignments": ["assignment_id", "offering_id"],
        "offerings": [
            "offering_id",
            "course_id",
            "term_id",
            "instructor_id",
        ],
        "courses": ["course_id", "department_id"],
        "instructors": ["instructor_id", "department_id"],
        "terms": ["term_id"],
    }

    local_tables = {
        "assignments": result,
        "offerings": offerings,
        "courses": courses,
        "instructors": instructors,
        "terms": terms,
    }

    for table_name, cols in key_columns.items():
        table = local_tables[table_name]

        for column in cols:
            if column in table.columns:
                table[column] = clean_id_series(table[column])

    result = (
        result
        .merge(
            offerings,
            on="offering_id",
            how="left",
            validate="many_to_one",
            suffixes=("", "_offering"),
        )
        .merge(
            courses,
            on="course_id",
            how="left",
            validate="many_to_one",
            suffixes=("", "_course"),
        )
        .merge(
            instructors,
            on="instructor_id",
            how="left",
            validate="many_to_one",
            suffixes=("", "_instructor"),
        )
        .merge(
            terms,
            on="term_id",
            how="left",
            validate="many_to_one",
            suffixes=("", "_term"),
        )
    )

    department_lookup = departments[
        ["department_id", "department_name"]
    ].copy()

    department_lookup["department_id"] = clean_id_series(
        department_lookup["department_id"]
    )

    result = result.merge(
        department_lookup,
        on="department_id",
        how="left",
        validate="many_to_one",
        suffixes=("", "_department"),
    )

    return result


def build_student_context(
    students: pd.DataFrame,
    majors: pd.DataFrame,
    departments: pd.DataFrame,
) -> pd.DataFrame:
    """Recreate the same student profile context used during training."""
    students = students.copy()
    majors = majors.copy()
    departments = departments.copy()

    students["student_id"] = clean_id_series(
        students["student_id"]
    )
    students["major_id"] = clean_id_series(
        students["major_id"]
    )

    majors["major_id"] = clean_id_series(
        majors["major_id"]
    )
    majors["department_id"] = clean_id_series(
        majors["department_id"]
    )

    departments["department_id"] = clean_id_series(
        departments["department_id"]
    )

    return (
        students
        .merge(
            majors,
            on="major_id",
            how="left",
            validate="many_to_one",
            suffixes=("", "_major"),
        )
        .merge(
            departments[
                ["department_id", "department_name"]
            ],
            on="department_id",
            how="left",
            validate="many_to_one",
            suffixes=("", "_department"),
        )
    )


def build_historical_behavior(
    behavior_events: pd.DataFrame,
    student_id: str,
    submitted_at: pd.Timestamp,
) -> dict[str, Any]:
    """Calculate the same historical event counts used by training."""
    events = behavior_events.copy()

    events["student_id"] = clean_id_series(
        events["student_id"]
    )

    events["event_date"] = pd.to_datetime(
        events["event_date"],
        errors="coerce",
    )

    student_events = events[
        (events["student_id"] == student_id)
        & (events["event_date"] < submitted_at)
    ].copy()

    recent_30 = student_events[
        student_events["event_date"]
        >= submitted_at - pd.Timedelta(days=30)
    ]

    recent_90 = student_events[
        student_events["event_date"]
        >= submitted_at - pd.Timedelta(days=90)
    ]

    event_types = [
        "AI Detector Flag",
        "Similarity Flag",
        "Unusual Collaboration",
        "Rapid Submission",
        "Plagiarism Flag",
        "Excessive Copy-Paste",
        "Repeated Revision Anomaly",
        "Peer Report",
        "Unauthorized File Sharing",
    ]

    output = {
        "prior_total_integrity_events": len(student_events),
        "prior_30d_integrity_events": len(recent_30),
        "prior_90d_integrity_events": len(recent_90),
    }

    for event_type in event_types:
        feature_name = (
            "prior_"
            + event_type.lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        output[feature_name] = int(
            (
                student_events["event_type"] == event_type
            ).sum()
        )

    return output


def build_history_snapshot(
    history: pd.DataFrame,
    student_id: str,
    submitted_at: pd.Timestamp,
) -> dict[str, Any]:
    """Return the most recent integrity snapshot strictly before submission."""
    history = history.copy()

    history["student_id"] = clean_id_series(
        history["student_id"]
    )

    history["snapshot_at"] = pd.to_datetime(
        history["snapshot_at"],
        errors="coerce",
    )

    history = history[
        history["snapshot_at"].notna()
    ].copy()

    columns = [
        "integrity_score",
        "trust_factor_score",
        "prior_confirmed_cases",
        "prior_dismissed_cases",
        "prior_suspicious_flags",
        "prior_ai_flags",
        "prior_plagiarism_flags",
        "prior_sanction_points",
        "recent_integrity_events",
        "integrity_status",
    ]

    output = {
        column: np.nan
        for column in columns
    }

    student_history = (
        history[
            history["student_id"] == student_id
        ]
        .sort_values("snapshot_at")
        .reset_index(drop=True)
    )

    if student_history.empty:
        return output

    prior_history = student_history[
        student_history["snapshot_at"] < submitted_at
    ]

    if prior_history.empty:
        return output

    latest = prior_history.iloc[-1]

    for column in columns:
        output[column] = latest.get(column, np.nan)

    return output


def build_detector_features(
    detector_inputs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Recreate the detector ensemble feature structure used by training.

    Inputs:
        detector_name -> {
            "probability": 0..1,
            "confidence": 0..1,
            "detected_as_ai": bool,
            "processing_success": bool
        }
    """
    rows = []

    for tool_name, values in detector_inputs.items():
        rows.append(
            {
                "tool_name": tool_name,
                "ai_probability": safe_float(
                    values["probability"],
                    0.0,
                ),
                "confidence_score": safe_float(
                    values["confidence"],
                    0.0,
                ),
                "detected_as_ai_numeric": int(
                    normalize_bool(values["detected_as_ai"])
                ),
                "processing_success": (
                    bool(values["processing_success"])
                ),
            }
        )

    detector_df = pd.DataFrame(rows)

    if detector_df.empty:
        return {
            "mean_detector_ai_probability": np.nan,
            "max_detector_ai_probability": np.nan,
            "min_detector_ai_probability": np.nan,
            "std_detector_ai_probability": np.nan,
            "mean_detector_confidence": np.nan,
            "max_detector_confidence": np.nan,
            "detectors_detecting_ai": np.nan,
            "detectors_available": 0,
            "detector_result_count": 0,
            "successful_detector_count": 0,
            "detector_ai_probability_range": np.nan,
            "detector_disagreement": np.nan,
        }

    output = {
        "mean_detector_ai_probability": detector_df[
            "ai_probability"
        ].mean(),

        "max_detector_ai_probability": detector_df[
            "ai_probability"
        ].max(),

        "min_detector_ai_probability": detector_df[
            "ai_probability"
        ].min(),

        "std_detector_ai_probability": detector_df[
            "ai_probability"
        ].std(),

        "mean_detector_confidence": detector_df[
            "confidence_score"
        ].mean(),

        "max_detector_confidence": detector_df[
            "confidence_score"
        ].max(),

        "detectors_detecting_ai": int(
            detector_df[
                "detected_as_ai_numeric"
            ].sum()
        ),

        "detectors_available": int(
            detector_df[
                "ai_probability"
            ].notna().sum()
        ),

        "detector_result_count": int(
            len(detector_df)
        ),

        "successful_detector_count": int(
            detector_df[
                "processing_success"
            ].sum()
        ),
    }

    output["detector_ai_probability_range"] = (
        output["max_detector_ai_probability"]
        -
        output["min_detector_ai_probability"]
    )

    output["detector_disagreement"] = (
        output["std_detector_ai_probability"]
        if not pd.isna(
            output["std_detector_ai_probability"]
        )
        else 0.0
    )

    # Same tool-specific probability columns generated by the
    # notebook's pivot/renaming logic.
    for _, row in detector_df.iterrows():
        column = (
            "detector_"
            + str(row["tool_name"])
            .strip()
            .lower()
            .replace(".", "")
            .replace(" ", "_")
            + "_ai_probability"
        )

        output[column] = safe_float(
            row["ai_probability"],
            np.nan,
        )

    return output


def parse_submission_timestamp(
    submitted_date,
    submitted_time,
) -> pd.Timestamp:
    """Combine date + time into a single Timestamp."""
    return pd.Timestamp(
        f"{submitted_date} {submitted_time}"
    )


def recalculate_engineered_features(
    row: pd.DataFrame,
) -> pd.DataFrame:
    """Recreate the engineered features from the training notebook."""
    result = row.copy()

    # Numeric safety
    for column in [
        "word_count",
        "expected_word_count",
        "max_word_count",
        "cited_references",
        "required_references",
        "editing_sessions",
        "revision_count",
        "draft_count",
        "time_spent_minutes",
        "vocabulary_richness",
        "lexical_diversity",
        "semantic_coherence",
        "perplexity_score",
        "burstiness_score",
        "typing_consistency",
        "detectors_available",
        "detector_result_count",
        "detectors_detecting_ai",
        "prior_confirmed_cases",
        "prior_dismissed_cases",
        "prior_90d_integrity_events",
        "prior_total_integrity_events",
        "number_of_edits",
    ]:
        if column in result.columns:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    # Word-count ratios
    result["word_count_vs_expected"] = (
        result["word_count"]
        /
        result["expected_word_count"].replace(
            0,
            np.nan,
        )
    )

    result["word_count_vs_max"] = (
        result["word_count"]
        /
        result["max_word_count"].replace(
            0,
            np.nan,
        )
    )

    result["word_count_deviation"] = (
        result["word_count"]
        -
        result["expected_word_count"]
    )

    # Citation behaviour
    result["citation_gap"] = (
        result["cited_references"]
        -
        result["required_references"]
    )

    result["references_per_1000_words"] = (
        result["cited_references"]
        /
        result["word_count"].clip(lower=1)
        * 1000
    )

    # Editing / effort behaviour
    result["edits_per_100_words"] = (
        result["editing_sessions"]
        /
        result["word_count"].clip(lower=1)
        * 100
    )

    result["revisions_per_100_words"] = (
        result["revision_count"]
        /
        result["word_count"].clip(lower=1)
        * 100
    )

    result["drafts_per_100_words"] = (
        result["draft_count"]
        /
        result["word_count"].clip(lower=1)
        * 100
    )

    result["words_per_minute"] = (
        result["word_count"]
        /
        result["time_spent_minutes"].clip(lower=1)
    )

    # Content profile
    result["linguistic_complexity"] = (
        (
            result["vocabulary_richness"]
            +
            result["lexical_diversity"]
            +
            result["semantic_coherence"]
        )
        / 3
    )

    result["ai_style_signal"] = (
        (
            result["perplexity_score"]
            +
            result["burstiness_score"]
            +
            result["typing_consistency"]
        )
        / 3
    )

    # Submission timing
    submitted_at = pd.to_datetime(
        result["submitted_at"],
        errors="coerce",
    )

    result["submission_hour"] = (
        submitted_at.dt.hour
    )

    result["submission_day_of_week"] = (
        submitted_at.dt.dayofweek
    )

    # Detector ensemble
    result["detector_coverage"] = (
        result["detectors_available"]
        /
        result["detector_result_count"].replace(
            0,
            np.nan,
        )
    )

    result["detector_ai_flag_rate"] = (
        result["detectors_detecting_ai"]
        /
        result["detectors_available"].replace(
            0,
            np.nan,
        )
    )

    # Student historical context
    result["prior_case_count"] = (
        result["prior_confirmed_cases"]
        +
        result["prior_dismissed_cases"]
    )

    result["prior_integrity_event_density"] = (
        result["prior_90d_integrity_events"]
        /
        result["prior_total_integrity_events"].replace(
            0,
            np.nan,
        )
    )

    return result


def apply_arrow_safe_types(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep runtime prediction DataFrame compatible with sklearn/pandas."""
    frame = frame.copy()

    for column in frame.columns:
        if frame[column].dtype == "object":
            frame[column] = frame[column].astype("string")

    return frame


def build_probability_gauge(probability: float) -> go.Figure:
    """Create a clean probability gauge."""
    percent = probability * 100

    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=percent,
            number={
                "suffix": "%",
                "font": {
                    "size": 34,
                    "color": "#F8FAFC",
                },
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": "#94a3b8",
                },
                "bar": {
                    "color": "#4f46e5",
                    "thickness": 0.28,
                },
                "bgcolor": "#e2e8f0",
                "borderwidth": 0,
            },
            title={
                "text": "AI-generation probability",
                "font": {
                    "size": 15,
                    "color": "#475569",
                },
            },
        )
    )

    figure.update_layout(
        height=290,
        margin={
            "l": 20,
            "r": 20,
            "t": 55,
            "b": 10,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Inter, sans-serif",
        },
    )

    return figure


def probability_status(probability: float) -> tuple[str, str]:
    """
    Produce neutral screening bands for the demo UI.

    These are interface bands, not institutional policy thresholds.
    """
    if probability >= 0.70:
        return (
            "Higher screening signal",
            "pill-high",
        )

    if probability >= 0.40:
        return (
            "Review recommended",
            "pill-review",
        )

    return (
        "Lower screening signal",
        "pill-low",
    )


def extract_global_feature_importance(
    pipeline,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Extract global model importance where supported.

    This is explicitly global model importance, not a per-row explanation.
    """
    try:
        preprocessor = pipeline.named_steps[
            "preprocessor"
        ]
        model = pipeline.named_steps[
            "model"
        ]

        names = preprocessor.get_feature_names_out()

        if hasattr(model, "feature_importances_"):
            values = model.feature_importances_

        elif hasattr(model, "coef_"):
            values = np.abs(
                np.asarray(
                    model.coef_
                )[0]
            )

        else:
            return pd.DataFrame()

        importance = (
            pd.DataFrame({
                "feature": names,
                "importance": values,
            })
            .sort_values(
                "importance",
                ascending=False,
            )
            .head(top_n)
            .reset_index(drop=True)
        )

        return importance

    except Exception:
        return pd.DataFrame()


def humanize_model_feature(name: str) -> str:
    """Convert sklearn transformed names to a readable label."""
    text = str(name)

    for prefix in [
        "numeric__",
        "categorical__",
    ]:
        if text.startswith(prefix):
            text = text.replace(prefix, "", 1)

    text = text.replace("_", " ")
    text = text.replace("=", ": ")
    return text.title()


# ============================================================
# LOAD DATA / MODEL
# ============================================================

@st.cache_resource(show_spinner=False)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Model artifact not found. "
            f"Expected: {MODEL_PATH}"
        )

    return joblib.load(
        MODEL_PATH
    )


@st.cache_data(show_spinner=False)
def load_reference_data():
    tables = {
        "academic_terms": load_csv(
            "academic_terms.csv"
        ),
        "departments": load_csv(
            "departments.csv"
        ),
        "majors": load_csv(
            "majors.csv"
        ),
        "instructors": load_csv(
            "instructors.csv"
        ),
        "students": load_csv(
            "students.csv"
        ),
        "courses": load_csv(
            "courses.csv"
        ),
        "course_offerings": load_csv(
            "course_offerings.csv"
        ),
        "assignments": load_csv(
            "assignments.csv"
        ),
        "submissions": load_csv(
            "submissions.csv"
        ),
        "detector_tools": load_csv(
            "detector_tools.csv"
        ),
        "ai_detector_results": load_csv(
            "ai_detector_results.csv"
        ),
        "student_behavior_events": load_csv(
            "student_behavior_events.csv"
        ),
        "integrity_cases": load_csv(
            "integrity_cases.csv"
        ),
        "student_integrity_history": load_csv(
            "student_integrity_history.csv"
        ),
    }

    return tables


@st.cache_data(show_spinner=False)
def load_ml_reference():
    if not ML_DATA_PATH.exists():
        raise FileNotFoundError(
            "ML reference dataset not found. "
            f"Expected: {ML_DATA_PATH}"
        )

    return pd.read_parquet(
        ML_DATA_PATH,
        engine="pyarrow",
    )


@st.cache_data(show_spinner=False)
def load_feature_manifest():
    if not MANIFEST_PATH.exists():
        return pd.DataFrame(
            columns=[
                "feature_name",
                "data_type",
                "feature_group",
            ]
        )

    return pd.read_csv(
        MANIFEST_PATH
    )


try:
    MODEL = load_model()
    TABLES = load_reference_data()
    ML_REFERENCE = load_ml_reference()
    FEATURE_MANIFEST = load_feature_manifest()

except Exception as exc:
    st.error(
        f"EduShield could not start correctly: {exc}"
    )

    st.info(
        "Make sure the processed CSVs, the ML Parquet file, and "
        "the saved model artifact exist in the project structure."
    )

    st.stop()


# ============================================================
# PREPARE CONTEXT TABLES
# ============================================================

students = TABLES["students"].copy()
majors = TABLES["majors"].copy()
departments = TABLES["departments"].copy()
assignments = TABLES["assignments"].copy()
course_offerings = TABLES["course_offerings"].copy()
courses = TABLES["courses"].copy()
instructors = TABLES["instructors"].copy()
terms = TABLES["academic_terms"].copy()
behavior_events = TABLES[
    "student_behavior_events"
].copy()
integrity_history = TABLES[
    "student_integrity_history"
].copy()


student_context = build_student_context(
    students,
    majors,
    departments,
)

assignment_context = build_assignment_context(
    assignments,
    course_offerings,
    courses,
    instructors,
    terms,
    departments,
)

students["student_id"] = clean_id_series(
    students["student_id"]
)

assignments["assignment_id"] = clean_id_series(
    assignments["assignment_id"]
)

assignment_context["assignment_id"] = clean_id_series(
    assignment_context["assignment_id"]
)

# ------------------------------------------------------------
# ML reference IDs
# ------------------------------------------------------------

if "student_id" in ML_REFERENCE.columns:
    ML_REFERENCE["student_id"] = clean_id_series(
        ML_REFERENCE["student_id"]
    )

if "assignment_id" in ML_REFERENCE.columns:
    ML_REFERENCE["assignment_id"] = clean_id_series(
        ML_REFERENCE["assignment_id"]
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        "## 🛡️ EduShield"
    )

    st.caption(
        "AI Submission Screening"
    )

    st.markdown("---")

    st.markdown(
        """
        <div class="sidebar-note">
        <strong>Demo workflow</strong><br><br>
        Select an existing student → select an academic assignment
        scenario → enter the new submission signals → enter detector
        evidence → generate a screening result.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    st.markdown(
        "**Model artifact**"
    )
    st.caption(
        MODEL_PATH.name
    )

    st.markdown(
        "**Dataset**"
    )
    st.caption(
        "Synthetic portfolio / research dataset"
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">EduShield • Intelligent Academic Integrity</div>
        <div class="hero-title">AI Submission Screening</div>
        <div class="hero-subtitle">
            Evaluate a newly submitted assignment using the student's existing
            academic profile, assignment context, submission behavior,
            historical integrity signals, and multi-detector AI evidence.
        </div>
        <div class="model-chip">
            <span class="model-dot"></span>
            Model pipeline ready
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="workflow">
        <div class="workflow-item">
            <span class="workflow-num">01</span>
            <span class="workflow-title">Profile</span>
            <span class="workflow-sub">Existing student</span>
        </div>
        <div class="workflow-item">
            <span class="workflow-num">02</span>
            <span class="workflow-title">Context</span>
            <span class="workflow-sub">Assignment & course</span>
        </div>
        <div class="workflow-item">
            <span class="workflow-num">03</span>
            <span class="workflow-title">Signals</span>
            <span class="workflow-sub">Submission & detectors</span>
        </div>
        <div class="workflow-item">
            <span class="workflow-num">04</span>
            <span class="workflow-title">Screen</span>
            <span class="workflow-sub">ML probability</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="warning-banner">
        <strong>Important:</strong> EduShield is built with synthetic data for
        portfolio/demo purposes. Its output is a screening indicator only and
        should not be used as an automatic disciplinary verdict.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# STUDENT + ASSIGNMENT SELECTION
# ============================================================

st.markdown(
    """
    <div class="section-header">
        <div class="section-number">01</div>
        <div>
            <div class="section-title">Select student & academic context</div>
            <div class="section-subtitle">Choose an existing profile and assignment scenario</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

selection_col1, selection_col2 = st.columns(
    [1.1, 1],
    gap="large",
)

with selection_col1:
    student_options = (
        student_context[
            "student_id"
        ]
        .dropna()
        .astype(str)
        .sort_values()
        .tolist()
    )

    selected_student_id = st.selectbox(
        "Existing student profile",
        options=student_options,
        index=0,
    )

with selection_col2:
    assignment_rows = (
        assignment_context[
            [
                "assignment_id",
                "assignment_title",
                "assignment_type",
                "subject_area",
            ]
        ]
        .drop_duplicates("assignment_id")
        .copy()
    )

    assignment_rows["display"] = (
        assignment_rows["assignment_id"].astype(str)
        + "  •  "
        + assignment_rows["assignment_title"].astype(str)
    )

    assignment_display_map = dict(
        zip(
            assignment_rows["display"],
            assignment_rows["assignment_id"],
        )
    )

    selected_assignment_display = st.selectbox(
        "Assignment scenario / template",
        options=assignment_rows[
            "display"
        ].tolist(),
        index=0,
    )

    selected_assignment_id = assignment_display_map[
        selected_assignment_display
    ]


selected_student = student_context[
    student_context["student_id"]
    == selected_student_id
].iloc[0]

selected_assignment = assignment_context[
    assignment_context["assignment_id"]
    == selected_assignment_id
].iloc[0]


# ============================================================
# PROFILE SUMMARY
# ============================================================

profile_cols = st.columns(5)

profile_metrics = [
    (
        profile_cols[0],
        "Student",
        selected_student_id,
        "Existing profile",
    ),
    (
        profile_cols[1],
        "Year level",
        prettify(
            selected_student.get(
                "year_level",
                "Unknown",
            )
        ),
        "Academic stage",
    ),
    (
        profile_cols[2],
        "Major",
        prettify(
            selected_student.get(
                "major_name",
                "Unknown",
            )
        ),
        "Program",
    ),
    (
        profile_cols[3],
        "GPA",
        f"{safe_float(selected_student.get('gpa', np.nan), np.nan):.2f}",
        "Current profile value",
    ),
    (
        profile_cols[4],
        "Attendance",
        f"{safe_float(selected_student.get('attendance_rate', np.nan), np.nan):.1f}%",
        "Current profile value",
    ),
]

for column, label, value, caption in profile_metrics:
    with column:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-caption">{caption}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


with st.expander(
    "View selected academic context",
    expanded=False,
):
    context_cols = st.columns(4)

    context_items = [
        (
            "Assignment",
            selected_assignment.get(
                "assignment_title",
                "Unknown",
            ),
        ),
        (
            "Type",
            selected_assignment.get(
                "assignment_type",
                "Unknown",
            ),
        ),
        (
            "Difficulty",
            selected_assignment.get(
                "difficulty_level",
                "Unknown",
            ),
        ),
        (
            "Subject",
            selected_assignment.get(
                "subject_area",
                "Unknown",
            ),
        ),
        (
            "Course",
            selected_assignment.get(
                "course_id",
                "Unknown",
            ),
        ),
        (
            "Instructor",
            selected_assignment.get(
                "instructor_id",
                "Unknown",
            ),
        ),
        (
            "Term",
            selected_assignment.get(
                "term_name",
                "Unknown",
            ),
        ),
        (
            "AI policy",
            selected_assignment.get(
                "ai_policy_adoption",
                "Unknown",
            ),
        ),
    ]

    for index, (label, value) in enumerate(context_items):
        with context_cols[index % 4]:
            st.markdown(
                f"**{label}**  \n"
                f"{prettify(value)}"
            )


# ============================================================
# DEFAULT HISTORICAL SUBMISSION
# ============================================================

student_history_rows = ML_REFERENCE[
    ML_REFERENCE["student_id"]
    == selected_student_id
].copy()

student_history_rows["submitted_at"] = pd.to_datetime(
    student_history_rows["submitted_at"],
    errors="coerce",
)

student_history_rows = (
    student_history_rows
    .sort_values("submitted_at")
    .reset_index(drop=True)
)

latest_historical_submission = (
    student_history_rows.iloc[-1]
    if not student_history_rows.empty
    else None
)


# ============================================================
# SUBMISSION TIMING
# ============================================================

st.markdown(
    """
    <div class="section-header">
        <div class="section-number">02</div>
        <div>
            <div class="section-title">New submission timing</div>
            <div class="section-subtitle">Set the simulated submission event</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

timing_col1, timing_col2, timing_col3 = st.columns(
    [1, 1, 1],
    gap="large",
)

assignment_open = pd.to_datetime(
    selected_assignment.get(
        "assignment_open_at",
        pd.NaT,
    ),
    errors="coerce",
)

assignment_deadline = pd.to_datetime(
    selected_assignment.get(
        "submission_deadline",
        pd.NaT,
    ),
    errors="coerce",
)

if pd.isna(assignment_deadline):
    default_submission = pd.Timestamp.now().replace(
        second=0,
        microsecond=0,
    )

else:
    default_submission = (
        assignment_deadline
        - pd.Timedelta(hours=24)
    )

default_submission_date = default_submission.date()
default_submission_time = default_submission.time().replace(
    second=0,
    microsecond=0,
)


with timing_col1:
    submitted_date = st.date_input(
        "Submission date",
        value=default_submission_date,
    )

with timing_col2:
    submitted_time = st.time_input(
        "Submission time",
        value=default_submission_time,
    )

with timing_col3:
    submission_status = st.selectbox(
        "Submission status",
        options=[
            "Submitted",
            "Resubmitted",
            "Late",
        ],
        index=0,
    )


submitted_at = parse_submission_timestamp(
    submitted_date,
    submitted_time,
)


hours_before_deadline = np.nan

if not pd.isna(assignment_deadline):
    hours_before_deadline = (
        (
            assignment_deadline
            -
            submitted_at
        ).total_seconds()
        / 3600
    )

late_submission = (
    bool(
        not pd.isna(assignment_deadline)
        and submitted_at > assignment_deadline
    )
)

if late_submission:
    st.markdown(
        """
        <div class="warning-banner">
            This simulated submission timestamp is after the selected
            assignment deadline, so EduShield will mark it as late.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SUBMISSION SIGNAL INPUTS
# ============================================================

st.markdown(
    """
    <div class="section-header">
        <div class="section-number">03</div>
        <div>
            <div class="section-title">Submission signals</div>
            <div class="section-subtitle">Describe the newly submitted work</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="info-banner">
        Enter the observed characteristics of the newly submitted work.
        Values are pre-filled from the selected student's latest historical
        submission where available, so you can adjust them to simulate a new case.
    </div>
    """,
    unsafe_allow_html=True,
)


def historical_default(
    column: str,
    fallback: float | int = 0,
) -> Any:
    if latest_historical_submission is None:
        return fallback

    value = latest_historical_submission.get(
        column,
        fallback,
    )

    if pd.isna(value) or value == "":
        return fallback

    return value


# ------------------------------------------------------------
# Writing / content
# ------------------------------------------------------------

st.markdown(
    """
    <div class="section-header" style="margin-top:0.8rem;">
        <div class="section-number" style="width:30px;height:30px;flex-basis:30px;border-radius:9px;">A</div>
        <div>
            <div class="section-title" style="font-size:0.94rem;">Writing & content profile</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

writing_col1, writing_col2, writing_col3, writing_col4 = st.columns(
    4,
    gap="large",
)

with writing_col1:
    word_count = st.number_input(
        "Word count",
        min_value=50,
        max_value=10000,
        value=max(
            50,
            safe_int(
                historical_default(
                    "word_count",
                    1200,
                ),
                1200,
            ),
        ),
        step=50,
    )

    avg_sentence_length = st.number_input(
        "Average sentence length",
        min_value=1.0,
        max_value=80.0,
        value=safe_float(
            historical_default(
                "avg_sentence_length",
                18.0,
            ),
            18.0,
        ),
        step=0.5,
    )

    paragraph_count = st.number_input(
        "Paragraph count",
        min_value=1,
        max_value=100,
        value=max(
            1,
            safe_int(
                historical_default(
                    "paragraph_count",
                    8,
                ),
                8,
            ),
        ),
        step=1,
    )

with writing_col2:
    sentence_length_std = st.number_input(
        "Sentence length variability",
        min_value=0.0,
        max_value=40.0,
        value=safe_float(
            historical_default(
                "sentence_length_std",
                6.0,
            ),
            6.0,
        ),
        step=0.5,
    )

    vocabulary_richness = st.number_input(
        "Vocabulary richness",
        min_value=0.0,
        max_value=1.0,
        value=np.clip(
            safe_float(
                historical_default(
                    "vocabulary_richness",
                    0.45,
                ),
                0.45,
            ),
            0.0,
            1.0,
        ),
        step=0.01,
    )

    lexical_diversity = st.number_input(
        "Lexical diversity",
        min_value=0.0,
        max_value=1.0,
        value=np.clip(
            safe_float(
                historical_default(
                    "lexical_diversity",
                    0.45,
                ),
                0.45,
            ),
            0.0,
            1.0,
        ),
        step=0.01,
    )

with writing_col3:
    repetition_ratio = st.number_input(
        "Repetition ratio",
        min_value=0.0,
        max_value=1.0,
        value=np.clip(
            safe_float(
                historical_default(
                    "repetition_ratio",
                    0.10,
                ),
                0.10,
            ),
            0.0,
            1.0,
        ),
        step=0.01,
    )

    grammar_error_rate = st.number_input(
        "Grammar error rate",
        min_value=0.0,
        max_value=1.0,
        value=np.clip(
            safe_float(
                historical_default(
                    "grammar_error_rate",
                    0.05,
                ),
                0.05,
            ),
            0.0,
            1.0,
        ),
        step=0.01,
    )

    semantic_coherence = st.number_input(
        "Semantic coherence",
        min_value=0.0,
        max_value=1.0,
        value=np.clip(
            safe_float(
                historical_default(
                    "semantic_coherence",
                    0.75,
                ),
                0.75,
            ),
            0.0,
            1.0,
        ),
        step=0.01,
    )

with writing_col4:
    perplexity_score = st.number_input(
        "Perplexity score",
        min_value=0.0,
        max_value=1.0,
        value=np.clip(
            safe_float(
                historical_default(
                    "perplexity_score",
                    0.50,
                ),
                0.50,
            ),
            0.0,
            1.0,
        ),
        step=0.01,
    )

    burstiness_score = st.number_input(
        "Burstiness score",
        min_value=0.0,
        max_value=1.0,
        value=np.clip(
            safe_float(
                historical_default(
                    "burstiness_score",
                    0.50,
                ),
                0.50,
            ),
            0.0,
            1.0,
        ),
        step=0.01,
    )

    typing_consistency = st.number_input(
        "Typing consistency",
        min_value=0.0,
        max_value=1.0,
        value=np.clip(
            safe_float(
                historical_default(
                    "typing_consistency",
                    0.65,
                ),
                0.65,
            ),
            0.0,
            1.0,
        ),
        step=0.01,
    )


# ------------------------------------------------------------
# Effort / editing
# ------------------------------------------------------------

st.markdown(
    """
    <div class="section-header" style="margin-top:1.05rem;">
        <div class="section-number" style="width:30px;height:30px;flex-basis:30px;border-radius:9px;">B</div>
        <div>
            <div class="section-title" style="font-size:0.94rem;">Effort, editing & citation behaviour</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

effort_col1, effort_col2, effort_col3, effort_col4 = st.columns(
    4,
    gap="large",
)

with effort_col1:
    editing_sessions = st.number_input(
        "Editing sessions",
        min_value=0,
        max_value=100,
        value=max(
            0,
            safe_int(
                historical_default(
                    "editing_sessions",
                    8,
                ),
                8,
            ),
        ),
    )

    revision_count = st.number_input(
        "Revision count",
        min_value=0,
        max_value=100,
        value=max(
            0,
            safe_int(
                historical_default(
                    "revision_count",
                    4,
                ),
                4,
            ),
        ),
    )

    draft_count = st.number_input(
        "Draft count",
        min_value=0,
        max_value=50,
        value=max(
            0,
            safe_int(
                historical_default(
                    "draft_count",
                    2,
                ),
                2,
            ),
        ),
    )

with effort_col2:
    time_spent_minutes = st.number_input(
        "Time spent (minutes)",
        min_value=5,
        max_value=10000,
        value=max(
            5,
            safe_int(
                historical_default(
                    "time_spent_minutes",
                    180,
                ),
                180,
            ),
        ),
        step=5,
    )

    number_of_edits = st.number_input(
        "Number of edits",
        min_value=0,
        max_value=5000,
        value=max(
            0,
            safe_int(
                historical_default(
                    "number_of_edits",
                    100,
                ),
                100,
            ),
        ),
        step=10,
    )

    copy_paste_ratio = st.number_input(
        "Copy / paste ratio",
        min_value=0.0,
        max_value=1.0,
        value=np.clip(
            safe_float(
                historical_default(
                    "copy_paste_ratio",
                    0.10,
                ),
                0.10,
            ),
            0.0,
            1.0,
        ),
        step=0.01,
    )

with effort_col3:
    cited_references = st.number_input(
        "Cited references",
        min_value=0,
        max_value=100,
        value=max(
            0,
            safe_int(
                historical_default(
                    "cited_references",
                    4,
                ),
                4,
            ),
        ),
    )

    citation_density = st.number_input(
        "Citation density",
        min_value=0.0,
        max_value=1.0,
        value=np.clip(
            safe_float(
                historical_default(
                    "citation_density",
                    0.20,
                ),
                0.20,
            ),
            0.0,
            1.0,
        ),
        step=0.01,
    )

    similarity_score = st.number_input(
        "Similarity score",
        min_value=0.0,
        max_value=1.0,
        value=np.clip(
            safe_float(
                historical_default(
                    "similarity_score",
                    0.10,
                ),
                0.10,
            ),
            0.0,
            1.0,
        ),
        step=0.01,
    )

with effort_col4:
    st.markdown(
        "**Assignment expectations**"
    )

    expected_word_count = safe_float(
        selected_assignment.get(
            "expected_word_count",
            historical_default(
                "expected_word_count",
                1200,
            ),
        ),
        1200,
    )

    max_word_count = safe_float(
        selected_assignment.get(
            "max_word_count",
            historical_default(
                "max_word_count",
                1500,
            ),
        ),
        1500,
    )

    required_references = safe_int(
        selected_assignment.get(
            "required_references",
            historical_default(
                "required_references",
                4,
            ),
        ),
        4,
    )

    st.metric(
        "Expected words",
        f"{expected_word_count:,.0f}",
    )

    st.metric(
        "Maximum words",
        f"{max_word_count:,.0f}",
    )

    st.metric(
        "Required references",
        f"{required_references}",
    )


# ============================================================
# AI DETECTOR INPUTS
# ============================================================

st.markdown(
    """
    <div class="section-header">
        <div class="section-number">04</div>
        <div>
            <div class="section-title">Multi-detector AI evidence</div>
            <div class="section-subtitle">Combine independent detector outputs into one ensemble signal</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="info-banner">
        Enter the AI probability and confidence reported by each detector.
        The AI flag is derived from the detector threshold used in the
        synthetic dataset, so the ensemble features stay consistent with
        training.
    </div>
    """,
    unsafe_allow_html=True,
)

detector_specs = [
    {
        "name": "GPTZero",
        "threshold": 0.50,
    },
    {
        "name": "Copyleaks",
        "threshold": 0.50,
    },
    {
        "name": "Turnitin",
        "threshold": 0.52,
    },
    {
        "name": "Originality.ai",
        "threshold": 0.56,
    },
    {
        "name": "Winston AI",
        "threshold": 0.49,
    },
]

detector_inputs: dict[str, dict[str, Any]] = {}

for row_start in range(0, len(detector_specs), 3):
    cols = st.columns(3, gap="large")

    for offset, column in enumerate(
        cols
    ):
        index = row_start + offset

        if index >= len(detector_specs):
            continue

        spec = detector_specs[index]

        with column:
            st.markdown(
                f"**{spec['name']}**"
            )

            probability_percent = st.slider(
                "AI probability",
                min_value=0,
                max_value=100,
                value=50,
                key=f"{spec['name']}_probability",
            )

            confidence_percent = st.slider(
                "Confidence",
                min_value=0,
                max_value=100,
                value=85,
                key=f"{spec['name']}_confidence",
            )

            probability = (
                probability_percent / 100
            )

            confidence = (
                confidence_percent / 100
            )

            detected_as_ai = (
                probability >= spec["threshold"]
            )

            detector_inputs[
                spec["name"]
            ] = {
                "probability": probability,
                "confidence": confidence,
                "detected_as_ai": detected_as_ai,
                "processing_success": True,
            }

            status_text = (
                "Flagged as AI"
                if detected_as_ai
                else "Not flagged"
            )

            st.caption(
                f"Threshold: {spec['threshold']:.2f} • "
                f"{status_text}"
            )


# ============================================================
# BUILD MODEL ROW
# ============================================================

def build_model_row() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build the single-row feature frame used by the saved pipeline."""

    # Start from the selected student's latest historical ML row
    # so every expected model column is present.
    if latest_historical_submission is not None:
        row = latest_historical_submission.to_dict()

    elif not ML_REFERENCE.empty:
        row = ML_REFERENCE.iloc[0].to_dict()

    else:
        row = {}

    row = pd.DataFrame(
        [row]
    )

    # --------------------------------------------------------
    # IDs / primary scenario
    # --------------------------------------------------------

    if "student_id" in row.columns:
        row.loc[0, "student_id"] = selected_student_id

    if "assignment_id" in row.columns:
        row.loc[0, "assignment_id"] = selected_assignment_id

    # --------------------------------------------------------
    # Current submission fields
    # --------------------------------------------------------

    submission_values = {
        "submitted_at": submitted_at,
        "submission_status": submission_status,
        "word_count": word_count,
        "cited_references": cited_references,
        "similarity_score": similarity_score,
        "late_submission": late_submission,
        "hours_before_deadline": hours_before_deadline,
        "editing_sessions": editing_sessions,
        "revision_count": revision_count,
        "draft_count": draft_count,
        "time_spent_minutes": time_spent_minutes,
        "copy_paste_ratio": copy_paste_ratio,
        "number_of_edits": number_of_edits,
        "typing_consistency": typing_consistency,
        "avg_sentence_length": avg_sentence_length,
        "sentence_length_std": sentence_length_std,
        "vocabulary_richness": vocabulary_richness,
        "lexical_diversity": lexical_diversity,
        "repetition_ratio": repetition_ratio,
        "paragraph_count": paragraph_count,
        "grammar_error_rate": grammar_error_rate,
        "citation_density": citation_density,
        "semantic_coherence": semantic_coherence,
        "perplexity_score": perplexity_score,
        "burstiness_score": burstiness_score,
    }

    for column, value in submission_values.items():
        if column in row.columns:
            row.loc[0, column] = value
        else:
            row[column] = value

    # --------------------------------------------------------
    # Assignment / course context
    # --------------------------------------------------------

    assignment_override_columns = [
        column
        for column in assignment_context.columns
        if column != "assignment_title"
    ]

    for column in assignment_override_columns:
        if column in row.columns:
            row.loc[
                0,
                column
            ] = selected_assignment.get(
                column,
                row.loc[0, column],
            )

    # Always use assignment-derived timing values
    if "assignment_open_at" in row.columns:
        row.loc[0, "assignment_open_at"] = (
            selected_assignment.get(
                "assignment_open_at",
                row.loc[0, "assignment_open_at"],
            )
        )

    if "submission_deadline" in row.columns:
        row.loc[0, "submission_deadline"] = (
            selected_assignment.get(
                "submission_deadline",
                row.loc[0, "submission_deadline"],
            )
        )

    if "expected_word_count" in row.columns:
        row.loc[0, "expected_word_count"] = (
            expected_word_count
        )

    if "max_word_count" in row.columns:
        row.loc[0, "max_word_count"] = (
            max_word_count
        )

    if "required_references" in row.columns:
        row.loc[0, "required_references"] = (
            required_references
        )

    # --------------------------------------------------------
    # Student context
    # --------------------------------------------------------

    student_override_columns = [
        "gender",
        "year_level",
        "major_id",
        "major_name",
        "department_name",
        "gpa",
        "attendance_rate",
        "academic_standing",
        "scholarship_status",
        "active_status",
    ]

    for column in student_override_columns:
        if (
            column in row.columns
            and column in selected_student.index
        ):
            row.loc[0, column] = selected_student[
                column
            ]

    # --------------------------------------------------------
    # Detector ensemble
    # --------------------------------------------------------

    detector_features = build_detector_features(
        detector_inputs
    )

    for column, value in detector_features.items():
        row.loc[0, column] = value

    # --------------------------------------------------------
    # Historical student behaviour
    # --------------------------------------------------------

    behavior_features = build_historical_behavior(
        behavior_events,
        selected_student_id,
        submitted_at,
    )

    for column, value in behavior_features.items():
        if column in row.columns:
            row.loc[0, column] = value
        else:
            row[column] = value

    # --------------------------------------------------------
    # Historical integrity snapshot
    # --------------------------------------------------------

    history_features = build_history_snapshot(
        integrity_history,
        selected_student_id,
        submitted_at,
    )

    for column, value in history_features.items():
        if column in row.columns:
            row.loc[0, column] = value
        else:
            row[column] = value

    # --------------------------------------------------------
    # Engineered features
    # --------------------------------------------------------

    row = recalculate_engineered_features(
        row
    )

    # --------------------------------------------------------
    # Use feature manifest to enforce exact model columns
    # --------------------------------------------------------

    if not FEATURE_MANIFEST.empty:
        expected_features = (
            FEATURE_MANIFEST[
                "feature_name"
            ]
            .dropna()
            .astype(str)
            .tolist()
        )

        for column in expected_features:
            if column not in row.columns:
                row[column] = np.nan

        row = row[
            expected_features
        ].copy()

    return (
        apply_arrow_safe_types(row),
        {
            "hours_before_deadline": hours_before_deadline,
            "late_submission": late_submission,
            "detector_features": detector_features,
            "behavior_features": behavior_features,
            "history_features": history_features,
        },
    )


# ============================================================
# PREDICTION
# ============================================================

st.markdown(
    """
    <div class="section-header">
        <div class="section-number">05</div>
        <div>
            <div class="section-title">Generate screening result</div>
            <div class="section-subtitle">Run the saved ML pipeline on the assembled feature vector</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

run_col1, run_col2 = st.columns(
    [4, 1],
    gap="large",
)

with run_col1:
    st.caption(
        "The saved training pipeline performs the same preprocessing "
        "and model inference used during model development."
    )

with run_col2:
    run_prediction = st.button(
        "🔍 Analyze Submission",
        type="primary",
        use_container_width=True,
    )


if run_prediction:

    try:
        model_row, diagnostics = (
            build_model_row()
        )

        probability = float(
            MODEL.predict_proba(
                model_row
            )[0, 1]
        )

        prediction = int(
            MODEL.predict(
                model_row
            )[0]
        )

        status_text, status_class = (
            probability_status(
                probability
            )
        )

        st.markdown(
            "---"
        )

        st.markdown(
            "## Screening result"
        )

        result_col1, result_col2 = st.columns(
            [1.05, 0.95],
            gap="large",
        )

        with result_col1:
            st.plotly_chart(
                build_probability_gauge(
                    probability
                ),
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )

        with result_col2:
            st.markdown(
                "<div class='section-card'>",
                unsafe_allow_html=True,
            )

            st.markdown(
                "<div class='mini-label'>MODEL OUTPUT</div>",
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="result-title">
                    {
                        "AI Generated"
                        if prediction == 1
                        else "Human Written"
                    }
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="status-pill {status_class}">
                    {status_text}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                "<br>",
                unsafe_allow_html=True,
            )

            st.metric(
                "AI probability",
                f"{probability * 100:.1f}%",
            )

            detector_consensus = (
                f"{diagnostics['detector_features'].get('detectors_detecting_ai', 0)} / "
                f"{diagnostics['detector_features'].get('detectors_available', 0)}"
            )

            st.metric(
                "Detector consensus",
                detector_consensus,
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------
        # Signal overview
        # ----------------------------------------------------

        st.markdown(
    """
    <div class="section-header" style="margin-top:1rem;">
        <div class="section-number" style="width:30px;height:30px;flex-basis:30px;border-radius:9px;">R</div>
        <div>
            <div class="section-title" style="font-size:0.94rem;">Evidence overview</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

        signal_cols = st.columns(
            4,
            gap="large",
        )

        detector_mean = safe_float(
            diagnostics["detector_features"].get(
                "mean_detector_ai_probability",
                np.nan,
            ),
            np.nan,
        )

        detector_confidence = safe_float(
            diagnostics["detector_features"].get(
                "mean_detector_confidence",
                np.nan,
            ),
            np.nan,
        )

        prior_events = safe_int(
            diagnostics["behavior_features"].get(
                "prior_total_integrity_events",
                0,
            ),
            0,
        )

        prior_cases = safe_int(
            diagnostics["history_features"].get(
                "prior_confirmed_cases",
                0,
            ),
            0,
        )

        signal_metrics = [
            (
                signal_cols[0],
                "Detector mean",
                (
                    f"{detector_mean * 100:.1f}%"
                    if not pd.isna(detector_mean)
                    else "N/A"
                ),
                "Mean AI probability",
            ),
            (
                signal_cols[1],
                "Detector confidence",
                (
                    f"{detector_confidence * 100:.1f}%"
                    if not pd.isna(detector_confidence)
                    else "N/A"
                ),
                "Mean tool confidence",
            ),
            (
                signal_cols[2],
                "Prior integrity events",
                f"{prior_events:,}",
                "Historical events before submission",
            ),
            (
                signal_cols[3],
                "Prior confirmed cases",
                f"{prior_cases:,}",
                "Historical confirmed cases",
            ),
        ]

        for column, label, value, caption in signal_metrics:
            with column:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{label}</div>
                        <div class="metric-value">{value}</div>
                        <div class="metric-caption">{caption}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # ----------------------------------------------------
        # Detector consensus
        # ----------------------------------------------------

        st.markdown(
    """
    <div class="section-header" style="margin-top:1rem;">
        <div class="section-number" style="width:30px;height:30px;flex-basis:30px;border-radius:9px;">D</div>
        <div>
            <div class="section-title" style="font-size:0.94rem;">Detector consensus</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

        detector_chart_rows = []

        for tool_name, values in detector_inputs.items():
            detector_chart_rows.append(
                {
                    "Detector": tool_name,
                    "AI probability":
                        values["probability"] * 100,
                }
            )

        detector_chart_df = pd.DataFrame(
            detector_chart_rows
        )

        st.bar_chart(
            detector_chart_df.set_index(
                "Detector"
            ),
            y="AI probability",
            height=290,
        )

        # ----------------------------------------------------
        # Global model importance
        # ----------------------------------------------------

        st.markdown(
    """
    <div class="section-header" style="margin-top:1rem;">
        <div class="section-number" style="width:30px;height:30px;flex-basis:30px;border-radius:9px;">M</div>
        <div>
            <div class="section-title" style="font-size:0.94rem;">Model signal profile</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

        st.caption(
            "These are global model-importance signals from the trained "
            "pipeline, not a causal explanation of this individual case."
        )

        importance_df = extract_global_feature_importance(
            MODEL,
            top_n=10,
        )

        if importance_df.empty:
            st.info(
                "Global feature importance is not exposed by the selected model."
            )

        else:
            importance_df["feature"] = (
                importance_df["feature"]
                .map(humanize_model_feature)
            )

            chart_df = importance_df.copy()

            st.bar_chart(
                chart_df.set_index("feature"),
                y="importance",
                height=340,
            )

        # ----------------------------------------------------
        # Submission summary
        # ----------------------------------------------------

        st.markdown(
    """
    <div class="section-header" style="margin-top:1rem;">
        <div class="section-number" style="width:30px;height:30px;flex-basis:30px;border-radius:9px;">S</div>
        <div>
            <div class="section-title" style="font-size:0.94rem;">Submission summary</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

        summary_data = pd.DataFrame(
            [
                {
                    "Student": selected_student_id,
                    "Assignment": selected_assignment_id,
                    "Submitted at":
                        submitted_at.strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    "Late":
                        "Yes"
                        if late_submission
                        else "No",
                    "Word count":
                        word_count,
                    "Time spent (min)":
                        time_spent_minutes,
                    "Similarity score":
                        f"{similarity_score:.3f}",
                    "Detector consensus":
                        f"{diagnostics['detector_features'].get('detectors_detecting_ai', 0)} / "
                        f"{diagnostics['detector_features'].get('detectors_available', 0)}",
                }
            ]
        )

        st.dataframe(
            summary_data,
            hide_index=True,
            use_container_width=True,
        )

        # ----------------------------------------------------
        # Download prediction package
        # ----------------------------------------------------

        prediction_package = model_row.copy()

        prediction_package[
            "prediction_is_ai_generated"
        ] = prediction

        prediction_package[
            "prediction_probability"
        ] = probability

        prediction_package[
            "screening_band"
        ] = status_text

        st.download_button(
            "⬇️ Download prediction record",
            data=prediction_package.to_csv(
                index=False
            ),
            file_name=(
                f"edushield_prediction_"
                f"{selected_student_id}_"
                f"{selected_assignment_id}.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )

        st.markdown(
            """
            <div class="info-banner">
                <strong>Interpretation:</strong> treat the result as a
                screening signal that should be reviewed alongside the original
                submission and institutional policy. The application does not
                make a disciplinary decision.
            </div>
            """,
            unsafe_allow_html=True,
        )

    except Exception as exc:
        st.error(
            "Prediction failed."
        )

        st.exception(
            exc
        )

        st.info(
            "If this is the first run after retraining, verify that the saved "
            "Parquet dataset, feature_manifest.csv, and model .joblib were "
            "generated by the same notebook version."
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    "---"
)

st.caption(
    "EduShield • Synthetic academic-integrity screening project • "
    "MySQL + Python + scikit-learn/XGBoost + Streamlit + Power BI"
)

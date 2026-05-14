"""
Simple Streamlit app for PMOS Lens.

The app is intentionally straightforward:
1. Collect the clinical features used by the trained model
2. Load the saved Random Forest model and preprocessor
3. Predict PMOS risk
4. Show the top contributing features and a domain-based summary
5. Add a pain-focused overlap guard for endometriosis-like concern

The comments are written for beginners so the prediction flow is easy to follow.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st


# Streamlit runs this file from the app folder, so we add the src directory to
# Python's import path before importing the existing model utilities.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from explain_model import explain_single_patient, load_model_and_preprocessor


REPORTS_PATH = PROJECT_ROOT / "reports"
METRICS_PATH = REPORTS_PATH / "metrics.json"

RISK_MODERATE_THRESHOLD = 0.20
RISK_HIGH_THRESHOLD = 0.50

# The training dataset stored cycle pattern as codes. The app hides the numeric
# codes from clinicians and presents human-readable options instead.
CYCLE_PATTERN_OPTIONS = {
    "Regular pattern": 2.0,
    "Irregular pattern": 4.0,
    "Marked irregularity": 5.0,
}

YES_NO_OPTIONS = {"No": 0.0, "Yes": 1.0}

FEATURE_LABELS = {
    "Age_yrs": "Age (years)",
    "Weight_Kg": "Weight (kg)",
    "Height_Cm": "Height (cm)",
    "BMI": "BMI",
    "Pulse_rate_bpm": "Pulse rate (bpm)",
    "RR_breaths_min": "Respiratory rate (breaths/min)",
    "Hb_g_dl": "Hemoglobin (g/dL)",
    "Cycle_R_I": "Cycle pattern",
    "Cycle_length_days": "Cycle length/duration in source dataset (days)",
    "FSH_mIU_mL": "FSH (mIU/mL)",
    "LH_mIU_mL": "LH (mIU/mL)",
    "FSH_LH": "FSH/LH ratio",
    "Hip_inch": "Hip circumference (inch)",
    "Waist_inch": "Waist circumference (inch)",
    "Waist_Hip_Ratio": "Waist:hip ratio",
    "TSH_mIU_L": "TSH (mIU/L)",
    "AMH_ng_mL": "AMH (ng/mL)",
    "PRL_ng_mL": "Prolactin (ng/mL)",
    "Vit_D3_ng_mL": "Vitamin D3 (ng/mL)",
    "PRG_ng_mL": "Progesterone (ng/mL)",
    "RBS_mg_dl": "Random blood sugar (mg/dL)",
    "Weight_gain_Y_N": "Recent weight gain",
    "hair_growth_Y_N": "Hair growth / hirsutism",
    "Skin_darkening_Y_N": "Skin darkening",
    "Hair_loss_Y_N": "Hair loss",
    "Pimples_Y_N": "Pimples / acne",
    "Fast_food_Y_N": "Frequent fast food intake",
    "Reg_Exercise_Y_N": "Regular exercise",
    "BP_Systolic_mmHg": "Systolic blood pressure (mmHg)",
    "BP_Diastolic_mmHg": "Diastolic blood pressure (mmHg)",
    "Follicle_No_L": "Follicle count - left ovary",
    "Follicle_No_R": "Follicle count - right ovary",
    "Avg_F_size_L_mm": "Average follicle size - left (mm)",
    "Avg_F_size_R_mm": "Average follicle size - right (mm)",
    "Endometrium_mm": "Endometrium thickness (mm)",
}

# Each feature belongs to one primary clinical domain so the app can summarize
# where the model's risk signal is concentrated.
FEATURE_TO_DOMAIN = {
    "Age_yrs": "reproductive",
    "Weight_Kg": "metabolic",
    "Height_Cm": "metabolic",
    "BMI": "metabolic",
    "Pulse_rate_bpm": "metabolic",
    "RR_breaths_min": "metabolic",
    "Hb_g_dl": "reproductive",
    "Cycle_R_I": "reproductive",
    "Cycle_length_days": "reproductive",
    "FSH_mIU_mL": "reproductive",
    "LH_mIU_mL": "reproductive",
    "FSH_LH": "reproductive",
    "Hip_inch": "metabolic",
    "Waist_inch": "metabolic",
    "Waist_Hip_Ratio": "metabolic",
    "TSH_mIU_L": "endocrine",
    "AMH_ng_mL": "ovarian",
    "PRL_ng_mL": "endocrine",
    "Vit_D3_ng_mL": "endocrine",
    "PRG_ng_mL": "reproductive",
    "RBS_mg_dl": "metabolic",
    "Weight_gain_Y_N": "metabolic",
    "hair_growth_Y_N": "dermatologic",
    "Skin_darkening_Y_N": "dermatologic",
    "Hair_loss_Y_N": "dermatologic",
    "Pimples_Y_N": "dermatologic",
    "Fast_food_Y_N": "metabolic",
    "Reg_Exercise_Y_N": "metabolic",
    "BP_Systolic_mmHg": "metabolic",
    "BP_Diastolic_mmHg": "metabolic",
    "Follicle_No_L": "ovarian",
    "Follicle_No_R": "ovarian",
    "Avg_F_size_L_mm": "ovarian",
    "Avg_F_size_R_mm": "ovarian",
    "Endometrium_mm": "ovarian",
}

DOMAIN_ORDER = [
    "reproductive",
    "endocrine",
    "metabolic",
    "ovarian",
    "dermatologic",
]


@st.cache_resource
def load_app_artifacts():
    """
    Load the saved Random Forest model, preprocessor, and optional metrics file.

    `st.cache_resource` keeps these heavy objects in memory so the app does not
    reload them on every click.
    """
    model, preprocessor = load_model_and_preprocessor()

    metrics = {}
    if METRICS_PATH.exists():
        with open(METRICS_PATH, "r", encoding="utf-8") as file_handle:
            metrics = json.load(file_handle)

    return model, preprocessor, metrics


def default_value(preprocessor, feature_name: str, fallback: float) -> float:
    """
    Use the saved training median as the default form value whenever possible.
    """
    return float(preprocessor.reference_values_.get(feature_name, fallback))


def yes_no_default(preprocessor, feature_name: str) -> int:
    """
    Convert a stored 0/1 default into the matching Streamlit selectbox index.
    """
    return 1 if default_value(preprocessor, feature_name, 0.0) >= 0.5 else 0


def cycle_default_index(preprocessor) -> int:
    """
    Choose the default cycle option based on the saved median cycle code.
    """
    cycle_code = default_value(preprocessor, "Cycle_R_I", 2.0)
    option_values = list(CYCLE_PATTERN_OPTIONS.values())
    if cycle_code in option_values:
        return option_values.index(cycle_code)
    return 0


def risk_category(probability: float) -> str:
    """
    Convert the raw model probability into a clinician-friendly triage band.
    """
    if probability < RISK_MODERATE_THRESHOLD:
        return "Low"
    if probability < RISK_HIGH_THRESHOLD:
        return "Moderate"
    return "High"


def feature_label(feature_name: str) -> str:
    """
    Return a readable label for display tables and reports.
    """
    return FEATURE_LABELS.get(feature_name, feature_name.replace("_", " "))


def build_domain_profile(explanation: Dict[str, object]) -> List[Dict[str, object]]:
    """
    Summarize where the positive risk signal is coming from.

    This is not a second diagnostic model. It is a structured grouping of the
    feature contributions that already came from the main model explanation.
    """
    contributions = explanation.get("all_feature_contributions", [])
    totals = {domain: 0.0 for domain in DOMAIN_ORDER}
    domain_drivers = {domain: [] for domain in DOMAIN_ORDER}

    for row in contributions:
        feature_name = row["feature"]
        contribution = float(row["contribution_to_risk"])
        if contribution <= 0:
            continue

        domain = FEATURE_TO_DOMAIN.get(feature_name)
        if not domain:
            continue

        totals[domain] += contribution
        domain_drivers[domain].append(row)

    total_positive_signal = sum(totals.values())
    profile_rows = []

    for domain in DOMAIN_ORDER:
        share_pct = 0.0
        if total_positive_signal > 0:
            share_pct = 100.0 * totals[domain] / total_positive_signal

        if share_pct >= 35:
            signal_label = "Dominant signal"
        elif share_pct >= 20:
            signal_label = "Supporting signal"
        elif share_pct > 0:
            signal_label = "Background signal"
        else:
            signal_label = "Quiet"

        top_domain_drivers = sorted(
            domain_drivers[domain],
            key=lambda row: row["contribution_to_risk"],
            reverse=True,
        )[:2]

        profile_rows.append(
            {
                "domain": domain,
                "signal_share_pct": share_pct,
                "signal_label": signal_label,
                "drivers": [feature_label(row["feature"]) for row in top_domain_drivers],
            }
        )

    return profile_rows


def build_overlap_guard(overlap_inputs: Dict[str, bool], category: str) -> Dict[str, str]:
    """
    Surface pain-dominant symptoms that may point to an endometriosis-like
    concern.

    These symptoms are not used by the trained model. They are shown separately
    as a safety-oriented guardrail so a low PMOS score does not hide a pain-led
    gynecologic concern.
    """
    pain_flags = sum(bool(value) for value in overlap_inputs.values())

    if pain_flags >= 2:
        headline = "Pain-dominant overlap flagged"
        detail = (
            "Two or more pain-dominant symptoms were reported. Consider an "
            "endometriosis-like overlap and clinical review for pain-focused "
            "differentials, even if the PMOS model output is not high."
        )
        status = "flag"
    elif pain_flags == 1:
        headline = "Single pain signal noted"
        detail = (
            "One pain-dominant symptom was reported. Track symptom pattern and "
            "consider broader gynecologic review if the pain history is strong "
            "or progressive."
        )
        status = "watch"
    else:
        headline = "No pain-dominant overlap signal captured"
        detail = (
            "No additional pain-focused symptoms were selected in the overlap "
            "guard section."
        )
        status = "clear"

    if category == "Low" and pain_flags >= 2:
        detail += " The low PMOS risk band should not reassure away pain-led evaluation."

    return {
        "status": status,
        "headline": headline,
        "detail": detail,
        "count": str(pain_flags),
    }


def format_contribution_table(rows: List[Dict[str, object]]) -> pd.DataFrame:
    """
    Convert explanation rows into a small table for Streamlit display.
    """
    if not rows:
        return pd.DataFrame(columns=["Feature", "Patient value", "Contribution"])

    return pd.DataFrame(
        [
            {
                "Feature": feature_label(row["feature"]),
                "Patient value": round(float(row["patient_value"]), 3),
                "Contribution": round(float(row["contribution_to_risk"]), 4),
            }
            for row in rows
        ]
    )


def display_contribution_rows(explanation: Dict[str, object]) -> List[Dict[str, object]]:
    """
    Choose the feature rows to display in the UI and report.

    Preferred behavior:
    - show the top risk-increasing features

    Fallback behavior:
    - if the patient has no positive drivers, show the largest absolute
      contributors so the explanation section never appears empty
    """
    top_increasing = explanation.get("top_5_risk_increasing_features", [])
    if top_increasing:
        return top_increasing

    return explanation.get("all_feature_contributions", [])[:5]


def generate_doctor_report(
    patient_id: str,
    probability: float,
    category: str,
    explanation: Dict[str, object],
    domain_profile: List[Dict[str, object]],
    overlap_guard: Dict[str, str],
) -> str:
    """
    Build a clinician-facing report that can be copied into a note or referral.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    report_rows = display_contribution_rows(explanation)
    contribution_heading = "Top features increasing modeled risk"
    if not explanation.get("top_5_risk_increasing_features"):
        contribution_heading = "Top absolute model contributors (mostly risk-reducing in this case)"

    top_feature_lines = []
    for rank, row in enumerate(report_rows, start=1):
        top_feature_lines.append(
            f"{rank}. {feature_label(row['feature'])} "
            f"(value {float(row['patient_value']):.2f}, contribution {float(row['contribution_to_risk']):.4f})"
        )

    domain_lines = []
    for row in domain_profile:
        drivers = ", ".join(row["drivers"]) if row["drivers"] else "No positive drivers captured"
        domain_lines.append(
            f"- {row['domain'].title()}: {row['signal_share_pct']:.1f}% of positive model signal; "
            f"{row['signal_label']}. Drivers: {drivers}."
        )

    report_text = f"""PMOS Lens doctor-ready triage summary
Generated: {timestamp}
Patient ID: {patient_id}

Terminology note:
PMOS is the updated name used in this app for the syndrome historically labeled as PCOS in the training dataset.

Clinical use statement:
This tool is for triage support only. It does not diagnose PMOS/PCOS and must not replace clinical judgment, examination, or confirmatory testing.

Model result:
- PMOS risk probability: {probability * 100:.1f}%
- Risk category: {category}
- Explanation method: {explanation['explanation_method']}

{contribution_heading}:
{chr(10).join(top_feature_lines) if top_feature_lines else "No positive feature drivers were identified."}

PMOS domain profile:
{chr(10).join(domain_lines)}

Overlap guard:
- Status: {overlap_guard['headline']}
- Detail: {overlap_guard['detail']}
- Pain-dominant symptom count captured outside the model: {overlap_guard['count']}

Interpretation note:
The domain profile groups the model's positive feature contributions into reproductive, endocrine, metabolic, ovarian, and dermatologic domains. The overlap guard is a safety prompt and is not part of the trained model score.
"""
    return report_text


def render_app() -> None:
    """
    Main Streamlit page.
    """
    st.set_page_config(page_title="PMOS Lens", layout="wide")

    st.title("PMOS Lens")
    st.markdown(
        "PMOS is the updated name used in this app for the condition historically "
        "labeled as PCOS in the training data."
    )
    st.warning(
        "This tool is for triage support only. It is not a diagnosis and does "
        "not replace clinical judgment, imaging review, or laboratory follow-up."
    )

    try:
        model, preprocessor, metrics = load_app_artifacts()
    except FileNotFoundError as error:
        st.error(f"Missing model artifact: {error}")
        st.info("Run `python run_pipeline.py` before launching the Streamlit app.")
        st.stop()

    st.caption(
        f"Loaded Random Forest model with {len(preprocessor.feature_names_)} features. "
        f"Reference triage threshold in the project reports: {metrics.get('decision_threshold', RISK_MODERATE_THRESHOLD):.2f}."
    )

    with st.form("pmos_patient_form"):
        st.subheader("Patient intake")

        patient_id = st.text_input(
            "Patient identifier",
            value="PATIENT_001",
            help="Optional identifier shown in the final report.",
        )

        st.markdown("#### Baseline measures")
        baseline_col1, baseline_col2, baseline_col3 = st.columns(3)
        age = baseline_col1.number_input(
            "Age (years)",
            min_value=10.0,
            max_value=60.0,
            value=default_value(preprocessor, "Age_yrs", 30.0),
            step=1.0,
        )
        weight = baseline_col2.number_input(
            "Weight (kg)",
            min_value=20.0,
            max_value=200.0,
            value=default_value(preprocessor, "Weight_Kg", 59.0),
            step=0.1,
        )
        height = baseline_col3.number_input(
            "Height (cm)",
            min_value=100.0,
            max_value=220.0,
            value=default_value(preprocessor, "Height_Cm", 156.0),
            step=0.1,
        )

        vital_col1, vital_col2, vital_col3 = st.columns(3)
        pulse = vital_col1.number_input(
            "Pulse rate (bpm)",
            min_value=30.0,
            max_value=200.0,
            value=default_value(preprocessor, "Pulse_rate_bpm", 72.0),
            step=1.0,
        )
        respiratory_rate = vital_col2.number_input(
            "Respiratory rate (breaths/min)",
            min_value=5.0,
            max_value=60.0,
            value=default_value(preprocessor, "RR_breaths_min", 18.0),
            step=1.0,
        )
        hemoglobin = vital_col3.number_input(
            "Hemoglobin (g/dL)",
            min_value=1.0,
            max_value=20.0,
            value=default_value(preprocessor, "Hb_g_dl", 11.0),
            step=0.1,
        )

        bmi = weight / ((height / 100.0) ** 2) if height > 0 else default_value(preprocessor, "BMI", 24.0)
        st.caption(f"Calculated BMI from weight and height: {bmi:.2f}")

        st.markdown("#### Reproductive and cycle history")
        reproductive_col1, reproductive_col2, reproductive_col3 = st.columns(3)
        cycle_pattern_label = reproductive_col1.selectbox(
            "Cycle pattern",
            options=list(CYCLE_PATTERN_OPTIONS.keys()),
            index=cycle_default_index(preprocessor),
            help="The app maps these options back to the cycle code used in the training data.",
        )
        cycle_length_days = reproductive_col2.number_input(
            "Cycle length/duration in source dataset (days)",
            min_value=0.0,
            max_value=20.0,
            value=default_value(preprocessor, "Cycle_length_days", 5.0),
            step=1.0,
        )
        progesterone = reproductive_col3.number_input(
            "Progesterone (ng/mL)",
            min_value=0.0,
            max_value=50.0,
            value=default_value(preprocessor, "PRG_ng_mL", 0.32),
            step=0.1,
        )

        hormone_col1, hormone_col2, hormone_col3 = st.columns(3)
        fsh = hormone_col1.number_input(
            "FSH (mIU/mL)",
            min_value=0.0,
            max_value=100.0,
            value=default_value(preprocessor, "FSH_mIU_mL", 4.865),
            step=0.1,
        )
        lh = hormone_col2.number_input(
            "LH (mIU/mL)",
            min_value=0.0,
            max_value=100.0,
            value=default_value(preprocessor, "LH_mIU_mL", 2.3),
            step=0.1,
        )
        endometrium = hormone_col3.number_input(
            "Endometrium thickness (mm)",
            min_value=0.0,
            max_value=30.0,
            value=default_value(preprocessor, "Endometrium_mm", 8.5),
            step=0.1,
        )

        fsh_lh_ratio = fsh / lh if lh > 0 else default_value(preprocessor, "FSH_LH", 2.2)
        st.caption(f"Calculated FSH/LH ratio: {fsh_lh_ratio:.2f}")

        st.markdown("#### Endocrine and metabolic markers")
        endocrine_col1, endocrine_col2, endocrine_col3 = st.columns(3)
        tsh = endocrine_col1.number_input(
            "TSH (mIU/L)",
            min_value=0.0,
            max_value=20.0,
            value=default_value(preprocessor, "TSH_mIU_L", 2.275),
            step=0.1,
        )
        amh = endocrine_col2.number_input(
            "AMH (ng/mL)",
            min_value=0.0,
            max_value=20.0,
            value=default_value(preprocessor, "AMH_ng_mL", 3.7),
            step=0.1,
        )
        prolactin = endocrine_col3.number_input(
            "Prolactin (ng/mL)",
            min_value=0.0,
            max_value=200.0,
            value=default_value(preprocessor, "PRL_ng_mL", 21.78),
            step=0.1,
        )

        metabolic_col1, metabolic_col2, metabolic_col3 = st.columns(3)
        vitamin_d = metabolic_col1.number_input(
            "Vitamin D3 (ng/mL)",
            min_value=0.0,
            max_value=100.0,
            value=default_value(preprocessor, "Vit_D3_ng_mL", 26.35),
            step=0.1,
        )
        rbs = metabolic_col2.number_input(
            "Random blood sugar (mg/dL)",
            min_value=20.0,
            max_value=400.0,
            value=default_value(preprocessor, "RBS_mg_dl", 100.0),
            step=1.0,
        )
        systolic_bp = metabolic_col3.number_input(
            "Systolic blood pressure (mmHg)",
            min_value=50.0,
            max_value=250.0,
            value=default_value(preprocessor, "BP_Systolic_mmHg", 110.0),
            step=1.0,
        )

        anthropometric_col1, anthropometric_col2, anthropometric_col3 = st.columns(3)
        diastolic_bp = anthropometric_col1.number_input(
            "Diastolic blood pressure (mmHg)",
            min_value=30.0,
            max_value=160.0,
            value=default_value(preprocessor, "BP_Diastolic_mmHg", 80.0),
            step=1.0,
        )
        waist = anthropometric_col2.number_input(
            "Waist circumference (inch)",
            min_value=10.0,
            max_value=100.0,
            value=default_value(preprocessor, "Waist_inch", 34.0),
            step=0.1,
        )
        hip = anthropometric_col3.number_input(
            "Hip circumference (inch)",
            min_value=10.0,
            max_value=100.0,
            value=default_value(preprocessor, "Hip_inch", 38.0),
            step=0.1,
        )

        waist_hip_ratio = waist / hip if hip > 0 else default_value(preprocessor, "Waist_Hip_Ratio", 0.89)
        st.caption(f"Calculated waist:hip ratio: {waist_hip_ratio:.3f}")

        st.markdown("#### Symptoms and lifestyle")
        symptom_col1, symptom_col2, symptom_col3, symptom_col4 = st.columns(4)
        weight_gain_label = symptom_col1.selectbox(
            "Recent weight gain",
            options=list(YES_NO_OPTIONS.keys()),
            index=yes_no_default(preprocessor, "Weight_gain_Y_N"),
        )
        hair_growth_label = symptom_col2.selectbox(
            "Hair growth / hirsutism",
            options=list(YES_NO_OPTIONS.keys()),
            index=yes_no_default(preprocessor, "hair_growth_Y_N"),
        )
        skin_darkening_label = symptom_col3.selectbox(
            "Skin darkening",
            options=list(YES_NO_OPTIONS.keys()),
            index=yes_no_default(preprocessor, "Skin_darkening_Y_N"),
        )
        hair_loss_label = symptom_col4.selectbox(
            "Hair loss",
            options=list(YES_NO_OPTIONS.keys()),
            index=yes_no_default(preprocessor, "Hair_loss_Y_N"),
        )

        lifestyle_col1, lifestyle_col2, lifestyle_col3 = st.columns(3)
        pimples_label = lifestyle_col1.selectbox(
            "Pimples / acne",
            options=list(YES_NO_OPTIONS.keys()),
            index=yes_no_default(preprocessor, "Pimples_Y_N"),
        )
        fast_food_label = lifestyle_col2.selectbox(
            "Frequent fast food intake",
            options=list(YES_NO_OPTIONS.keys()),
            index=yes_no_default(preprocessor, "Fast_food_Y_N"),
        )
        exercise_label = lifestyle_col3.selectbox(
            "Regular exercise",
            options=list(YES_NO_OPTIONS.keys()),
            index=yes_no_default(preprocessor, "Reg_Exercise_Y_N"),
        )

        st.markdown("#### Ovarian ultrasound profile")
        ovarian_col1, ovarian_col2, ovarian_col3, ovarian_col4 = st.columns(4)
        follicle_left = ovarian_col1.number_input(
            "Follicle count - left ovary",
            min_value=0.0,
            max_value=50.0,
            value=default_value(preprocessor, "Follicle_No_L", 5.0),
            step=1.0,
        )
        follicle_right = ovarian_col2.number_input(
            "Follicle count - right ovary",
            min_value=0.0,
            max_value=50.0,
            value=default_value(preprocessor, "Follicle_No_R", 6.0),
            step=1.0,
        )
        follicle_size_left = ovarian_col3.number_input(
            "Average follicle size - left (mm)",
            min_value=0.0,
            max_value=40.0,
            value=default_value(preprocessor, "Avg_F_size_L_mm", 15.0),
            step=0.1,
        )
        follicle_size_right = ovarian_col4.number_input(
            "Average follicle size - right (mm)",
            min_value=0.0,
            max_value=40.0,
            value=default_value(preprocessor, "Avg_F_size_R_mm", 16.0),
            step=0.1,
        )

        st.markdown("#### Overlap guard for pain-dominant symptoms")
        st.caption(
            "These symptoms do not change the model score. They are shown as a "
            "separate guardrail for possible endometriosis-like overlap."
        )
        overlap_col1, overlap_col2, overlap_col3 = st.columns(3)
        severe_period_pain = overlap_col1.checkbox("Severe period pain")
        chronic_pelvic_pain = overlap_col2.checkbox("Chronic pelvic pain")
        pain_with_intercourse = overlap_col3.checkbox("Pain with intercourse")

        overlap_col4, overlap_col5 = st.columns(2)
        pain_with_bowel_symptoms = overlap_col4.checkbox("Pain with bowel symptoms or bloating")
        pain_between_periods = overlap_col5.checkbox("Pain between periods")

        submitted = st.form_submit_button("Assess PMOS risk")

    if not submitted:
        return

    patient_feature_values = {
        "Age_yrs": age,
        "Weight_Kg": weight,
        "Height_Cm": height,
        "BMI": bmi,
        "Pulse_rate_bpm": pulse,
        "RR_breaths_min": respiratory_rate,
        "Hb_g_dl": hemoglobin,
        "Cycle_R_I": CYCLE_PATTERN_OPTIONS[cycle_pattern_label],
        "Cycle_length_days": cycle_length_days,
        "FSH_mIU_mL": fsh,
        "LH_mIU_mL": lh,
        "FSH_LH": fsh_lh_ratio,
        "Hip_inch": hip,
        "Waist_inch": waist,
        "Waist_Hip_Ratio": waist_hip_ratio,
        "TSH_mIU_L": tsh,
        "AMH_ng_mL": amh,
        "PRL_ng_mL": prolactin,
        "Vit_D3_ng_mL": vitamin_d,
        "PRG_ng_mL": progesterone,
        "RBS_mg_dl": rbs,
        "Weight_gain_Y_N": YES_NO_OPTIONS[weight_gain_label],
        "hair_growth_Y_N": YES_NO_OPTIONS[hair_growth_label],
        "Skin_darkening_Y_N": YES_NO_OPTIONS[skin_darkening_label],
        "Hair_loss_Y_N": YES_NO_OPTIONS[hair_loss_label],
        "Pimples_Y_N": YES_NO_OPTIONS[pimples_label],
        "Fast_food_Y_N": YES_NO_OPTIONS[fast_food_label],
        "Reg_Exercise_Y_N": YES_NO_OPTIONS[exercise_label],
        "BP_Systolic_mmHg": systolic_bp,
        "BP_Diastolic_mmHg": diastolic_bp,
        "Follicle_No_L": follicle_left,
        "Follicle_No_R": follicle_right,
        "Avg_F_size_L_mm": follicle_size_left,
        "Avg_F_size_R_mm": follicle_size_right,
        "Endometrium_mm": endometrium,
    }

    patient_df = pd.DataFrame([patient_feature_values])

    explanation = explain_single_patient(
        model=model,
        preprocessor=preprocessor,
        patient_row=patient_df,
        patient_id=patient_id or "Unspecified patient",
        top_n=5,
    )

    probability = float(explanation["predicted_probability"])
    category = risk_category(probability)
    domain_profile = build_domain_profile(explanation)
    overlap_inputs = {
        "severe_period_pain": severe_period_pain,
        "chronic_pelvic_pain": chronic_pelvic_pain,
        "pain_with_intercourse": pain_with_intercourse,
        "pain_with_bowel_symptoms": pain_with_bowel_symptoms,
        "pain_between_periods": pain_between_periods,
    }
    overlap_guard = build_overlap_guard(overlap_inputs, category)
    report_text = generate_doctor_report(
        patient_id=patient_id or "Unspecified patient",
        probability=probability,
        category=category,
        explanation=explanation,
        domain_profile=domain_profile,
        overlap_guard=overlap_guard,
    )
    contribution_rows = display_contribution_rows(explanation)

    st.subheader("PMOS triage output")
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("PMOS risk percentage", f"{probability * 100:.1f}%")
    metric_col2.metric("Risk category", category)
    metric_col3.metric("Explanation method", explanation["explanation_method"])

    if category == "High":
        st.error("High PMOS risk band: expedite clinician review and follow-up testing.")
    elif category == "Moderate":
        st.warning("Moderate PMOS risk band: triage for further assessment and confirmatory review.")
    else:
        st.success("Low PMOS risk band: low modeled signal, but clinical context still matters.")

    st.markdown("#### Top contributing features")
    if explanation["top_5_risk_increasing_features"]:
        st.caption("These are the strongest features pushing the prediction toward higher PMOS risk.")
    else:
        st.caption("No positive drivers dominated this case, so the table shows the largest absolute contributors.")
    st.dataframe(
        format_contribution_table(contribution_rows),
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("#### PMOS domain profile")
    st.caption("Share of the model's positive risk signal grouped into five clinical domains.")
    domain_columns = st.columns(len(DOMAIN_ORDER))
    for column, row in zip(domain_columns, domain_profile):
        with column:
            st.metric(row["domain"].title(), f"{row['signal_share_pct']:.0f}%")
            st.caption(row["signal_label"])
            if row["drivers"]:
                st.caption("Drivers: " + ", ".join(row["drivers"]))

    st.markdown("#### Overlap guard")
    if overlap_guard["status"] == "flag":
        st.error(overlap_guard["headline"] + ": " + overlap_guard["detail"])
    elif overlap_guard["status"] == "watch":
        st.warning(overlap_guard["headline"] + ": " + overlap_guard["detail"])
    else:
        st.info(overlap_guard["headline"] + ": " + overlap_guard["detail"])

    st.markdown("#### Doctor-ready report")
    st.text_area(
        "Summary report",
        value=report_text,
        height=420,
    )
    st.download_button(
        label="Download report",
        data=report_text,
        file_name=f"{(patient_id or 'patient').replace(' ', '_')}_pmos_report.txt",
        mime="text/plain",
    )


if __name__ == "__main__":
    render_app()

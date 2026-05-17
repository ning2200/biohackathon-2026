import json
import os
import re
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

from flask import Flask, jsonify, request
import pandas as pd

project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from explain_model import explain_single_patient, load_model_and_preprocessor

app = Flask(__name__)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = os.getenv("OPENAI_API_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is required for the backend LLM call.")

model, preprocessor = load_model_and_preprocessor()


def float_or_none(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def bool_to_flag(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    normalized = str(value).strip().lower()
    if normalized in {
        "yes",
        "true",
        "1",
        "present",
        "positive",
        "some",
        "mild",
        "moderate",
        "severe",
        "significant",
        "often",
        "frequent",
    }:
        return 1.0
    if normalized in {
        "no",
        "false",
        "0",
        "absent",
        "negative",
        "none",
        "never",
    }:
        return 0.0
    return None


def cycle_pattern_code(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    normalized = str(value).strip().lower()
    if normalized in {"regular", "regular pattern", "regular cycle"}:
        return 2.0
    if normalized in {"irregular", "irregular pattern", "irregular cycle"}:
        return 4.0
    if normalized in {"marked irregularity", "marked irregular", "marked", "absent", "amenorrhea"}:
        return 5.0
    return float_or_none(value)


def calculate_bmi(weight_kg: Optional[float], height_cm: Optional[float]) -> Optional[float]:
    if weight_kg is None or height_cm is None or height_cm == 0.0:
        return None
    return round(weight_kg / ((height_cm / 100.0) ** 2), 1)


def calculate_ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator is None or denominator == 0.0:
        return None
    return round(numerator / denominator, 2)


def calculate_waist_hip_ratio(waist_inch: Optional[float], hip_inch: Optional[float]) -> Optional[float]:
    if waist_inch is None or hip_inch is None or hip_inch == 0.0:
        return None
    return round(waist_inch / hip_inch, 3)


def build_patient_feature_row(payload: Dict[str, Any]) -> Dict[str, Optional[float]]:
    weight_kg = float_or_none(payload.get("weight_kg"))
    height_cm = float_or_none(payload.get("height_cm"))
    fsh = float_or_none(payload.get("fsh"))
    lh = float_or_none(payload.get("lh"))
    waist_inch = float_or_none(payload.get("waist_inch"))
    hip_inch = float_or_none(payload.get("hip_inch"))

    bmi_value = float_or_none(payload.get("bmi")) or calculate_bmi(weight_kg, height_cm)
    fsh_lh_value = float_or_none(payload.get("fsh_lh")) or calculate_ratio(fsh, lh)
    waist_hip_ratio_value = float_or_none(payload.get("waist_hip_ratio")) or calculate_waist_hip_ratio(waist_inch, hip_inch)

    return {
        "Age_yrs": float_or_none(payload.get("patient_age")),
        "Weight_Kg": weight_kg,
        "Height_Cm": height_cm,
        "BMI": bmi_value,
        "Pulse_rate_bpm": float_or_none(payload.get("pulse_rate")),
        "RR_breaths_min": float_or_none(payload.get("respiratory_rate")),
        "Hb_g_dl": float_or_none(payload.get("hemoglobin")),
        "Cycle_R_I": cycle_pattern_code(payload.get("menstrual_regularity")),
        "Cycle_length_days": float_or_none(payload.get("cycle_length")),
        "FSH_mIU_mL": fsh,
        "LH_mIU_mL": lh,
        "FSH_LH": fsh_lh_value,
        "Hip_inch": hip_inch,
        "Waist_inch": waist_inch,
        "Waist_Hip_Ratio": waist_hip_ratio_value,
        "TSH_mIU_L": float_or_none(payload.get("tsh")),
        "AMH_ng_mL": float_or_none(payload.get("amh")),
        "PRL_ng_mL": float_or_none(payload.get("prl")),
        "Vit_D3_ng_mL": float_or_none(payload.get("vit_d3")),
        "PRG_ng_mL": float_or_none(payload.get("prg")),
        "RBS_mg_dl": float_or_none(payload.get("fasting_glucose")),
        "Weight_gain_Y_N": bool_to_flag(payload.get("weight_gain")),
        "hair_growth_Y_N": bool_to_flag(payload.get("hirsutism")),
        "Skin_darkening_Y_N": bool_to_flag(payload.get("skin_darkening")),
        "Hair_loss_Y_N": bool_to_flag(payload.get("hair_loss")),
        "Pimples_Y_N": bool_to_flag(payload.get("acne")),
        "Fast_food_Y_N": bool_to_flag(payload.get("fast_food")),
        "Reg_Exercise_Y_N": bool_to_flag(payload.get("regular_exercise")),
        "BP_Systolic_mmHg": float_or_none(payload.get("systolic_bp")),
        "BP_Diastolic_mmHg": float_or_none(payload.get("diastolic_bp")),
        "Follicle_No_L": float_or_none(payload.get("follicle_count_left")),
        "Follicle_No_R": float_or_none(payload.get("follicle_count_right")),
        "Avg_F_size_L_mm": float_or_none(payload.get("avg_f_size_left")),
        "Avg_F_size_R_mm": float_or_none(payload.get("avg_f_size_right")),
        "Endometrium_mm": float_or_none(payload.get("endometrium_mm")),
    }


def extract_json_object(text: str) -> Dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("LLM response did not contain a valid JSON object.")
    return json.loads(match.group(0))


def call_openai(prompt: str) -> Dict[str, Any]:
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a clinical reasoning assistant. Use only the provided patient data "
                    "and the machine learning model output to produce a valid JSON object."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.0,
        "max_tokens": 1000,
    }

    request_data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    request = urllib.request.Request(OPENAI_API_URL, data=request_data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_text = response.read().decode("utf-8")
            response_json = json.loads(response_text)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"OpenAI request failed: {exc.code} {exc.reason} {body}") from exc

    assistant = (
        response_json.get("choices", [])[0]
        .get("message", {})
        .get("content")
        if response_json.get("choices")
        else None
    )

    if not assistant:
        raise RuntimeError("OpenAI response did not contain assistant content.")

    return extract_json_object(assistant.strip())


def build_llm_prompt(payload: Dict[str, Any], explanation: Dict[str, Any]) -> str:
    lines: List[str] = [
        "PATIENT INPUT:",
    ]

    mapping = [
        ("patient_id", "Patient ID"),
        ("patient_age", "Age (yrs)"),
        ("weight_kg", "Weight (kg)"),
        ("height_cm", "Height (cm)"),
        ("menstrual_regularity", "Menstrual regularity"),
        ("cycle_length", "Cycle length (days)"),
        ("bmi", "BMI"),
        ("weight_gain", "Recent weight gain"),
        ("hirsutism", "Hirsutism"),
        ("acne", "Acne"),
        ("fsh", "FSH (IU/L)"),
        ("lh", "LH (IU/L)"),
        ("fsh_lh", "FSH/LH ratio"),
        ("amh", "AMH (ng/mL)"),
        ("follicle_count_left", "Follicle count left"),
        ("follicle_count_right", "Follicle count right"),
        ("waist_hip_ratio", "Waist:hip ratio"),
        ("fasting_glucose", "Fasting blood glucose (mg/dL)"),
        ("systolic_bp", "Systolic BP (mmHg)"),
        ("diastolic_bp", "Diastolic BP (mmHg)"),
    ]

    for key, label in mapping:
        if payload.get(key) is not None and payload.get(key) != "":
            value = payload[key]
            if isinstance(value, bool):
                value = "Yes" if value else "No"
            lines.append(f"- {label}: {value}")

    lines.extend([
        "\nMODEL OUTPUT:",
        f"- Predicted probability: {explanation['predicted_probability']:.4f}",
        f"- Risk label: {explanation['risk_label']}",
        f"- Explanation method: {explanation['explanation_method']}",
        "- Top increasing feature contributions:",
    ])

    for row in explanation.get("top_5_risk_increasing_features", []):
        lines.append(
            f"  - {row['feature']}: value={row['patient_value']}, contribution={row['contribution_to_risk']:.4f}"
        )

    lines.extend([
        "\nINSTRUCTIONS:",
        "Use the clinical data and the model outputs to generate a JSON-only clinical reasoning summary.",
        "Do not include any explanatory text outside the JSON object.",
        "Return exactly these fields: risk_level, top_reasons, next_steps, full_explanation.",
        "risk_level must be one of: low, moderate, high.",
        "top_reasons should be 3-6 concise clinical drivers.",
        "next_steps should be 2-5 specific clinical recommendations.",
        "full_explanation should be 2-4 paragraphs and mention missing data if relevant.",
    ])

    return "\n".join(lines)


def normalize_model_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "risk_level": payload.get("risk_level"),
        "top_reasons": payload.get("top_reasons"),
        "next_steps": payload.get("next_steps"),
        "full_explanation": payload.get("full_explanation"),
    }


@app.route("/api/assessments", methods=["POST"])
def create_assessment():
    payload = request.get_json(force=True)
    if not payload:
        return jsonify({"error": "Missing JSON payload."}), 400

    patient_id = payload.get("patient_id", "unknown")
    feature_row = build_patient_feature_row(payload)
    patient_df = pd.DataFrame([feature_row])

    explanation = explain_single_patient(
        model=model,
        preprocessor=preprocessor,
        patient_row=patient_df,
        patient_id=patient_id,
        top_n=5,
    )

    prompt = build_llm_prompt(payload, explanation)
    llm_result = call_openai(prompt)
    llm_response = normalize_model_response(llm_result)

    response_payload = {
        "patient_id": patient_id,
        "model_probability": explanation["predicted_probability"],
        "model_risk_label": explanation["risk_label"],
        "model_explanation_method": explanation["explanation_method"],
        "model_top_increasing_features": explanation.get("top_5_risk_increasing_features", []),
        **llm_response,
    }
    return jsonify(response_payload)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

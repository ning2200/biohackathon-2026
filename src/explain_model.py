"""
PMOS Lens - Random Forest Explainability

This module explains the final Random Forest model in two ways:
1. Global importance: which features matter most across many patients
2. Local explanation: which features increased risk for one patient

The code prefers SHAP when it is installed because SHAP gives a principled
per-feature contribution. If SHAP is not available, the module falls back to a
simple model-based method so the pipeline still works.
"""

import json
import pickle
import warnings
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from pmos_pipeline import MODELS_PATH, REPORTS_PATH, PMOSPreprocessor, load_dataset

try:
    import shap

    SHAP_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on the local environment
    shap = None
    SHAP_AVAILABLE = False
    warnings.warn(
        "SHAP is not installed. Falling back to model-based explanations.",
        stacklevel=2,
    )


RANDOM_FOREST_MODEL_PATH = MODELS_PATH / "pmos_random_forest_model.pkl"
PREPROCESSOR_PATH = MODELS_PATH / "pmos_preprocessor.pkl"
GLOBAL_IMPORTANCE_PATH = REPORTS_PATH / "global_feature_importance.json"
SAMPLE_EXPLANATION_PATH = REPORTS_PATH / "sample_patient_explanation.json"


def load_pickle_artifact(path: Path) -> Any:
    """
    Read a pickled model artifact from disk.
    """
    if not path.exists():
        raise FileNotFoundError(f"Required artifact not found: {path}")

    with open(path, "rb") as file_handle:
        return pickle.load(file_handle)


def load_model_and_preprocessor(
    model_path: Path = RANDOM_FOREST_MODEL_PATH,
    preprocessor_path: Path = PREPROCESSOR_PATH,
) -> Tuple[Any, PMOSPreprocessor]:
    """
    Load the trained Random Forest model and the matching preprocessor.

    Keeping these together is important:
    the model expects features in the same cleaned order that the preprocessor
    learned during training.
    """
    model = load_pickle_artifact(model_path)
    preprocessor = load_pickle_artifact(preprocessor_path)

    print(f"Loaded Random Forest model from {model_path}")
    print(f"Loaded preprocessor from {preprocessor_path}")
    return model, preprocessor


def load_reference_data(preprocessor: PMOSPreprocessor) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load raw dataset rows and transform them into model-ready features.

    We reuse the original dataset so global explainability and sample patient
    explanations reflect the same clinical schema used during training.
    """
    raw_df = load_dataset()
    processed_features = preprocessor.transform(raw_df)
    return raw_df, processed_features


def extract_positive_class_shap_values(shap_values: Any) -> np.ndarray:
    """
    Normalize SHAP output into a 2D array for the positive PCOS class.

    Different SHAP versions return slightly different shapes, so this helper
    keeps the rest of the code simple.
    """
    if isinstance(shap_values, list):
        return np.asarray(shap_values[1])

    shap_array = np.asarray(shap_values)
    if shap_array.ndim == 3:
        return shap_array[:, :, 1]

    return shap_array


def generate_global_feature_importance(
    model: Any,
    processed_features: pd.DataFrame,
    top_n: int = 20,
) -> Dict[str, Any]:
    """
    Rank features by overall importance.

    Preferred path:
    - SHAP mean absolute contribution across many patients

    Fallback path:
    - Random Forest built-in `feature_importances_`
    """
    sampled_features = processed_features.sample(
        n=min(len(processed_features), 200),
        random_state=42,
    )

    if SHAP_AVAILABLE:
        explainer = shap.TreeExplainer(model)
        shap_values = extract_positive_class_shap_values(explainer.shap_values(sampled_features))
        importance_scores = np.abs(shap_values).mean(axis=0)
        method = "shap_mean_absolute_value"
        method_note = (
            "Each score is the average size of that feature's SHAP contribution "
            "across sampled patients."
        )
    else:
        importance_scores = model.feature_importances_
        method = "random_forest_feature_importance"
        method_note = (
            "SHAP was unavailable, so the scores come from the Random Forest's "
            "built-in split importance."
        )

    ranked_features = sorted(
        [
            {
                "feature": feature_name,
                "importance": float(score),
            }
            for feature_name, score in zip(processed_features.columns, importance_scores)
        ],
        key=lambda item: item["importance"],
        reverse=True,
    )

    result = {
        "method": method,
        "method_note": method_note,
        "top_features": ranked_features[:top_n],
    }
    return result


def estimate_local_feature_effects_without_shap(
    model: Any,
    patient_features: pd.DataFrame,
    preprocessor: PMOSPreprocessor,
) -> np.ndarray:
    """
    Fallback patient-level explanation when SHAP is missing.

    Idea:
    1. Predict the patient's risk using the real feature values
    2. Replace one feature at a time with a typical training value
    3. Measure how much the risk drops or rises

    A positive result means that the patient's real value pushed the prediction
    toward higher PCOS risk.
    """
    baseline_probability = model.predict_proba(patient_features)[0, 1]
    local_effects: List[float] = []

    for feature_name in patient_features.columns:
        modified_patient = patient_features.copy()
        modified_patient.at[patient_features.index[0], feature_name] = preprocessor.reference_values_.get(
            feature_name,
            patient_features.iloc[0][feature_name],
        )
        modified_probability = model.predict_proba(modified_patient)[0, 1]
        local_effects.append(float(baseline_probability - modified_probability))

    return np.asarray(local_effects)


def explain_single_patient(
    model: Any,
    preprocessor: PMOSPreprocessor,
    patient_row: pd.DataFrame,
    patient_id: str,
    top_n: int = 5,
) -> Dict[str, Any]:
    """
    Explain one patient's prediction.

    The returned object highlights the top `top_n` features that increased risk.
    """
    if len(patient_row) != 1:
        raise ValueError("patient_row must contain exactly one row.")

    processed_patient = preprocessor.transform(patient_row)
    probability = float(model.predict_proba(processed_patient)[0, 1])
    predicted_class = int(model.predict(processed_patient)[0])

    if SHAP_AVAILABLE:
        explainer = shap.TreeExplainer(model)
        shap_values = extract_positive_class_shap_values(explainer.shap_values(processed_patient))[0]
        explanation_method = "shap_tree_explainer"
        explanation_note = (
            "Positive SHAP values push the prediction toward higher PCOS risk. "
            "Negative values pull it downward."
        )
        local_effects = shap_values
    else:
        explanation_method = "one_feature_replacement_fallback"
        explanation_note = (
            "SHAP was unavailable, so each contribution shows how much the risk "
            "changed when one feature was replaced with a typical training value."
        )
        local_effects = estimate_local_feature_effects_without_shap(
            model=model,
            patient_features=processed_patient,
            preprocessor=preprocessor,
        )

    feature_rows = []
    for feature_name, patient_value, contribution in zip(
        processed_patient.columns,
        processed_patient.iloc[0],
        local_effects,
    ):
        feature_rows.append(
            {
                "feature": feature_name,
                "patient_value": float(patient_value),
                "contribution_to_risk": float(contribution),
                "direction": "increases_risk" if contribution > 0 else "decreases_risk",
            }
        )

    all_feature_contributions = sorted(
        feature_rows,
        key=lambda row: abs(row["contribution_to_risk"]),
        reverse=True,
    )

    top_increasing = sorted(
        [row for row in feature_rows if row["contribution_to_risk"] > 0],
        key=lambda row: row["contribution_to_risk"],
        reverse=True,
    )[:top_n]

    top_decreasing = sorted(
        [row for row in feature_rows if row["contribution_to_risk"] < 0],
        key=lambda row: row["contribution_to_risk"],
    )[:top_n]

    return {
        "patient_id": patient_id,
        "predicted_probability": probability,
        "predicted_class": predicted_class,
        "risk_label": "High Risk" if probability >= 0.5 else "Low Risk",
        "explanation_method": explanation_method,
        "explanation_note": explanation_note,
        "all_feature_contributions": all_feature_contributions,
        "top_5_risk_increasing_features": top_increasing,
        "top_5_risk_reducing_features": top_decreasing,
    }


def save_json_report(payload: Dict[str, Any], output_path: Path) -> None:
    """
    Save a JSON report with UTF-8 encoding for easy reuse by other tools.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, indent=2)


def main(patient_index: int = 0) -> Dict[str, Any]:
    """
    Run the full explanation pipeline and save the sample patient JSON.

    Workflow:
    1. Load the Random Forest model and preprocessor
    2. Build global feature importance
    3. Explain one patient row from the dataset
    4. Save the explanation JSON files into `reports/`
    """
    print()
    print("=" * 70)
    print("PMOS LENS - RANDOM FOREST EXPLAINABILITY")
    print("=" * 70)
    print()

    model, preprocessor = load_model_and_preprocessor()
    raw_df, processed_features = load_reference_data(preprocessor)

    print("=" * 70)
    print("STEP 1: GLOBAL FEATURE IMPORTANCE")
    print("=" * 70)
    global_importance = generate_global_feature_importance(model, processed_features)
    for rank, feature_row in enumerate(global_importance["top_features"][:10], start=1):
        print(f"{rank:2d}. {feature_row['feature']:30s} {feature_row['importance']:.4f}")
    print()

    print("=" * 70)
    print("STEP 2: PATIENT-LEVEL EXPLANATION")
    print("=" * 70)
    patient_row = raw_df.iloc[[patient_index]].copy()
    patient_id = f"SAMPLE_{patient_index:03d}"
    patient_explanation = explain_single_patient(
        model=model,
        preprocessor=preprocessor,
        patient_row=patient_row,
        patient_id=patient_id,
        top_n=5,
    )

    print(f"Patient ID: {patient_explanation['patient_id']}")
    print(f"Predicted probability: {patient_explanation['predicted_probability']:.4f}")
    print(f"Risk label: {patient_explanation['risk_label']}")
    print(f"Explanation method: {patient_explanation['explanation_method']}")
    print()
    print("Top 5 features increasing risk:")
    for rank, feature_row in enumerate(patient_explanation["top_5_risk_increasing_features"], start=1):
        print(
            f"{rank:2d}. {feature_row['feature']:30s} "
            f"value={feature_row['patient_value']:.4f} "
            f"contribution={feature_row['contribution_to_risk']:.4f}"
        )
    print()

    explanation_payload = {
        "patient_explanation": patient_explanation,
        "global_feature_importance_summary": global_importance,
    }

    save_json_report(global_importance, GLOBAL_IMPORTANCE_PATH)
    save_json_report(explanation_payload, SAMPLE_EXPLANATION_PATH)

    print(f"Saved global importance report to {GLOBAL_IMPORTANCE_PATH}")
    print(f"Saved sample patient explanation to {SAMPLE_EXPLANATION_PATH}")
    print()

    return explanation_payload


if __name__ == "__main__":
    main()

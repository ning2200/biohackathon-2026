#!/usr/bin/env python
"""
PMOS Lens - Explainability Module Visualization

This script shows the overall flow of the explainability pipeline.
Run with: python visualize_pipeline.py
"""

def print_architecture():
    """Print the overall system architecture"""
    
    architecture = """
╔════════════════════════════════════════════════════════════════════════════╗
║                    PMOS LENS - SYSTEM ARCHITECTURE                         ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌──────────────────────────────────────────────────────────────────┐     ║
║  │ INPUT: Patient Clinical Data                                    │     ║
║  │ (Age, BMI, Hormones, Ultrasound, Symptoms, etc.)               │     ║
║  └─────────────────────┬──────────────────────────────────────────┘     ║
║                        │                                                 ║
║                        ▼                                                 ║
║  ┌──────────────────────────────────────────────────────────────────┐     ║
║  │ TRAINED RANDOM FOREST MODEL                                     │     ║
║  │ (pmos_risk_model.pkl)                                           │     ║
║  │                                                                  │     ║
║  │ ✓ 100 decision trees                                            │     ║
║  │ ✓ Feature interactions learned                                  │     ║
║  │ ✓ Optimized decision threshold                                  │     ║
║  └─────────────────────┬──────────────────────────────────────────┘     ║
║                        │                                                 ║
║         ┌──────────────┴──────────────┐                                  ║
║         │                             │                                  ║
║         ▼                             ▼                                  ║
║  ┌─────────────────┐         ┌──────────────────┐                       ║
║  │ PREDICTION:     │         │ EXPLANATION:     │                       ║
║  │                 │         │ SHAP VALUES      │                       ║
║  │ Probability:    │         │                  │                       ║
║  │ 72% PCOS Risk   │         │ TreeExplainer    │                       ║
║  │                 │         │ ↓                │                       ║
║  │ Risk Level:     │         │ Shapley Values   │                       ║
║  │ HIGH            │         │ for each feature │                       ║
║  └────────┬────────┘         └────────┬─────────┘                       ║
║           │                          │                                  ║
║           └──────────────┬───────────┘                                  ║
║                          ▼                                              ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │ OUTPUT: Clinical Explanation                                    │   ║
║  ├──────────────────────────────────────────────────────────────────┤   ║
║  │                                                                  │   ║
║  │ TOP 5 RISK-INCREASING FACTORS:                                  │   ║
║  │ 1. AMH: 5.8 ng/mL → +0.34 (Increases Risk)                     │   ║
║  │ 2. Hair Growth → +0.12 (Increases Risk)                        │   ║
║  │ 3. Irregular Cycles → +0.08 (Increases Risk)                   │   ║
║  │ ...                                                             │   ║
║  │                                                                  │   ║
║  │ PROTECTIVE FACTORS:                                             │   ║
║  │ • Regular Exercise → -0.10 (Decreases Risk)                    │   ║
║  │                                                                  │   ║
║  │ CLINICAL RECOMMENDATION:                                        │   ║
║  │ → Refer to endocrinologist                                      │   ║
║  │ → Suggest ultrasound confirmation                              │   ║
║  │ → Patient lifestyle counseling                                 │   ║
║  │                                                                  │   ║
║  └──────────────────────────────────────────────────────────────────┘   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""
    print(architecture)


def print_explanation_types():
    """Print the two types of explanations"""
    
    types = """
╔════════════════════════════════════════════════════════════════════════════╗
║           TWO TYPES OF EXPLAINABILITY (SHAP)                              ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │ GLOBAL EXPLAINABILITY (Model-Level)                                │  ║
║  ├─────────────────────────────────────────────────────────────────────┤  ║
║  │                                                                     │  ║
║  │ Question: "What does the model use overall?"                       │  ║
║  │                                                                     │  ║
║  │ Method:                                                            │  ║
║  │   1. Calculate SHAP values for all training samples                │  ║
║  │   2. Take mean |SHAP value| for each feature                       │  ║
║  │   3. Rank by magnitude                                             │  ║
║  │                                                                     │  ║
║  │ Output:                                                            │  ║
║  │   Rank  Feature          Importance                                │  ║
║  │   ────────────────────────────────────                             │  ║
║  │   1.    AMH              0.0847  ████████████████  (8.5%)          │  ║
║  │   2.    FSH/LH           0.0723  █████████████    (7.2%)           │  ║
║  │   3.    BMI              0.0651  ████████████     (6.5%)           │  ║
║  │   ...                                                              │  ║
║  │                                                                     │  ║
║  │ Use: Understand model priorities, validate clinical relevance     │  ║
║  │                                                                     │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │ LOCAL EXPLAINABILITY (Patient-Level)                               │  ║
║  ├─────────────────────────────────────────────────────────────────────┤  ║
║  │                                                                     │  ║
║  │ Question: "Why this prediction for this patient?"                  │  ║
║  │                                                                     │  ║
║  │ Method:                                                            │  ║
║  │   1. Pass patient through Random Forest                            │  ║
║  │   2. Calculate path through trees                                  │  ║
║  │   3. Compute SHAP value contribution per feature                   │  ║
║  │   4. Sort by magnitude                                             │  ║
║  │                                                                     │  ║
║  │ Output (for Patient JANE DOE):                                     │  ║
║  │   Base probability: 50%                                            │  ║
║  │   +0.25 (AMH = 5.8)              → 75%  ⬆ Risk Up                  │  ║
║  │   +0.10 (Hair Growth = Yes)      → 85%  ⬆ Risk Up                  │  ║
║  │   -0.05 (Regular Exercise = Yes) → 80%  ⬇ Risk Down               │  ║
║  │   ...                                                              │  ║
║  │   Final prediction: 72% PCOS Risk                                  │  ║
║  │                                                                     │  ║
║  │ Use: Explain individual predictions, generate patient reports     │  ║
║  │                                                                     │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""
    print(types)


def print_workflow():
    """Print the user workflow"""
    
    workflow = """
╔════════════════════════════════════════════════════════════════════════════╗
║                     USER WORKFLOW                                         ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  STEP 1: TRAIN THE MODEL                                                  ║
║  ┌────────────────────────────────────────────────────────────────────┐   ║
║  │ $ python run_pipeline.py                                           │   ║
║  │                                                                    │   ║
║  │ ✓ Loads dataset from data/raw/                                   │   ║
║  │ ✓ Trains Random Forest on 432 patients                           │   ║
║  │ ✓ Evaluates on 109 test patients                                 │   ║
║  │ ✓ Saves: models/pmos_risk_model.pkl                             │   ║
║  │ ✓ Saves: reports/metrics.json                                   │   ║
║  │ ✓ Saves: reports/feature_importance.png                         │   ║
║  │                                                                    │   ║
║  │ Time: ~30-60 seconds                                             │   ║
║  └────────────────────────────────────────────────────────────────────┘   ║
║                                              ▼                            ║
║  STEP 2: GENERATE EXPLANATIONS                                            ║
║  ┌────────────────────────────────────────────────────────────────────┐   ║
║  │ $ python run_explain.py                                            │   ║
║  │                                                                    │   ║
║  │ ✓ Loads trained model                                            │   ║
║  │ ✓ Calculates global feature importance                           │   ║
║  │ ✓ Generates sample patient explanation (SHAP)                   │   ║
║  │ ✓ Saves: reports/sample_patient_explanation.json               │   ║
║  │ ✓ Saves: reports/global_feature_importance.json                │   ║
║  │ ✓ Displays formatted explanation to console                    │   ║
║  │                                                                    │   ║
║  │ Time: ~2-5 seconds                                               │   ║
║  └────────────────────────────────────────────────────────────────────┘   ║
║                                              ▼                            ║
║  STEP 3: INTEGRATE INTO APPLICATION                                       ║
║  ┌────────────────────────────────────────────────────────────────────┐   ║
║  │ from explain_model import explain_single_prediction               │   ║
║  │                                                                    │   ║
║  │ # Load model                                                      │   ║
║  │ model = load_trained_model()                                      │   ║
║  │                                                                    │   ║
║  │ # For each patient:                                              │   ║
║  │ explanation = explain_single_prediction(                          │   ║
║  │     model,                                                        │   ║
║  │     patient_data,                                                 │   ║
║  │     patient_id='P123'                                             │   ║
║  │ )                                                                 │   ║
║  │                                                                    │   ║
║  │ # Display to clinician                                           │   ║
║  │ print(format_explanation_for_display(explanation))               │   ║
║  │                                                                    │   ║
║  │ # Save to medical record                                         │   ║
║  │ save_to_ehr(explanation)                                          │   ║
║  └────────────────────────────────────────────────────────────────────┘   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""
    print(workflow)


def print_interpretation_guide():
    """Print interpretation guide for SHAP values"""
    
    guide = """
╔════════════════════════════════════════════════════════════════════════════╗
║              HOW TO INTERPRET SHAP VALUES                                 ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  VALUE INTERPRETATION                                                     ║
║  ─────────────────────────────────────────────────────────────────────    ║
║                                                                            ║
║  SHAP Value = Contribution to Prediction                                  ║
║  (How much this feature changes the prediction)                           ║
║                                                                            ║
║  Example: Interpreting "AMH" with SHAP value +0.34                       ║
║  ┌────────────────────────────────────────────────────────────────────┐   ║
║  │                                                                    │   ║
║  │  50%  ←──────────── Base Prediction (no info)                    │   ║
║  │  │                                                               │   ║
║  │  │     "This patient has AMH = 5.8"                             │   ║
║  │  ├─ +0.34 ──→ Model adds +34 percentage points to prediction    │   ║
║  │  │                                                               │   ║
║  │  84%  ←──────────── New Prediction (with AMH info)              │   ║
║  │                                                                    │   ║
║  │  INTERPRETATION:                                                 │   ║
║  │  "High AMH increases PCOS probability by +34 points"            │   ║
║  │                                                                    │   ║
║  └────────────────────────────────────────────────────────────────────┘   ║
║                                                                            ║
║  SIGN INTERPRETATION                                                      ║
║  ─────────────────────────────────────────────────────────────────────    ║
║                                                                            ║
║  Positive SHAP Value (+)    →    Increases Risk    →    Bad for PCOS    ║
║  Negative SHAP Value (-)    →    Decreases Risk   →    Good for PCOS    ║
║                                                                            ║
║  Example:                                                                 ║
║  Feature: "Regular_exercise"                                              ║
║  Patient Value: 1 (Yes, exercises regularly)                              ║
║  SHAP Value: -0.08                                                        ║
║  Interpretation: "Regular exercise reduces PCOS risk by -8 points"       ║
║                                                                            ║
║                                                                            ║
║  MAGNITUDE INTERPRETATION                                                 ║
║  ─────────────────────────────────────────────────────────────────────    ║
║                                                                            ║
║  |SHAP Value| = Strength of Influence                                     ║
║                                                                            ║
║  |0.0001| ≤ Very weak          (almost no impact)                         ║
║  |0.005| ≤ Weak                (small impact)                             ║
║  |0.05|  ≤ Moderate            (noticeable impact)                        ║
║  |0.15|  ≤ Strong              (important influence)                      ║
║  |0.25|  ≤ Very strong         (major determinant)                        ║
║                                                                            ║
║  Example Patient Explanation:                                             ║
║  ────────────────────────────────────────────────────────────────────     ║
║                                                                            ║
║  Predicted Risk: 72%                                                      ║
║                                                                            ║
║  Feature             Value    SHAP    Interpretation                      ║
║  ─────────────────────────────────────────────────────────────────        ║
║  AMH_ng_mL           5.8    +0.34    Very Strong Risk Factor             ║
║  FSH_LH              0.7    +0.18    Strong Risk Factor                  ║
║  Hair_growth         1.0    +0.08    Moderate Risk Factor               ║
║  Pimples             1.0    +0.02    Weak Risk Factor                   ║
║  Regular_exercise    0.0    -0.10    Moderate Protective Factor         ║
║                                                                            ║
║  CLINICAL SUMMARY:                                                        ║
║  Multiple strong risk factors converge. Recommend specialist evaluation. ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""
    print(guide)


def print_files_generated():
    """Print information about generated files"""
    
    files = """
╔════════════════════════════════════════════════════════════════════════════╗
║                    FILES GENERATED BY EXPLAINABILITY MODULE               ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  AFTER: python run_pipeline.py                                            ║
║  ─────────────────────────────────────────────────────────────────────    ║
║                                                                            ║
║  models/pmos_risk_model.pkl                                               ║
║  └─ Trained Random Forest model (binary format)                           ║
║     Use: Load with pickle.load() for predictions                          ║
║                                                                            ║
║  reports/metrics.json                                                     ║
║  └─ Model performance metrics (JSON format)                               ║
║     Contains: Accuracy, Precision, Recall, Specificity, AUC-ROC, CM      ║
║                                                                            ║
║  reports/feature_importance.png                                           ║
║  └─ Bar plot of top 20 features (image)                                   ║
║     Shows: Feature importance scores visually                             ║
║                                                                            ║
║                                                                            ║
║  AFTER: python run_explain.py                                             ║
║  ─────────────────────────────────────────────────────────────────────    ║
║                                                                            ║
║  reports/sample_patient_explanation.json  ✨ NEW                          ║
║  └─ SHAP-based explanation for example patient                            ║
║     Contains:                                                             ║
║       - Patient ID and predicted risk                                     ║
║       - Top 5 risk-increasing factors (with SHAP values)                 ║
║       - Top 5 protective factors (with SHAP values)                      ║
║       - All features with contributions                                  ║
║       - Explanation method (SHAP or tree-based)                          ║
║                                                                            ║
║     Example Content:                                                      ║
║     {                                                                     ║
║       "patient_id": "SAMPLE_001",                                        ║
║       "predicted_probability": 0.72,                                     ║
║       "risk_level": "High Risk",                                         ║
║       "top_risk_factors": [                                              ║
║         {                                                                ║
║           "feature": "AMH_ng_mL",                                       ║
║           "patient_value": 5.8,                                         ║
║           "contribution": 0.34                                          ║
║         },                                                              ║
║         ...                                                             ║
║       ]                                                                 ║
║     }                                                                     ║
║                                                                            ║
║  reports/global_feature_importance.json  ✨ NEW                           ║
║  └─ Global feature importance ranking                                     ║
║     Contains:                                                             ║
║       - All features ranked by overall importance                         ║
║       - Importance scores (higher = more important)                       ║
║                                                                            ║
║     Example Content:                                                      ║
║     {                                                                     ║
║       "AMH_ng_mL": 0.0847,                                               ║
║       "FSH_LH": 0.0723,                                                  ║
║       "BMI": 0.0651,                                                     ║
║       ...                                                                ║
║     }                                                                     ║
║                                                                            ║
║                                                                            ║
║  HOW TO USE THESE FILES                                                   ║
║  ─────────────────────────────────────────────────────────────────────    ║
║                                                                            ║
║  1. Review sample explanation:                                            ║
║     $ cat reports/sample_patient_explanation.json                         ║
║                                                                            ║
║  2. Use in your application:                                              ║
║     import json                                                           ║
║     with open('reports/sample_patient_explanation.json') as f:           ║
║         explanation = json.load(f)                                       ║
║                                                                            ║
║  3. Generate new explanations on-the-fly:                                 ║
║     from src.explain_model import explain_single_prediction               ║
║     new_explanation = explain_single_prediction(model, patient_data)      ║
║                                                                            ║
║  4. Store for medical records:                                            ║
║     ehr_system.save_explanation(patient_id, explanation)                  ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""
    print(files)


def main():
    """Run all visualizations"""
    print("\n" * 2)
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "PMOS LENS - EXPLAINABILITY MODULE VISUALIZATION".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    
    print("\n\nSECTION 1: SYSTEM ARCHITECTURE")
    print_architecture()
    
    input("\nPress Enter to continue to SECTION 2...")
    
    print("\n\nSECTION 2: EXPLANATION TYPES")
    print_explanation_types()
    
    input("\nPress Enter to continue to SECTION 3...")
    
    print("\n\nSECTION 3: USER WORKFLOW")
    print_workflow()
    
    input("\nPress Enter to continue to SECTION 4...")
    
    print("\n\nSECTION 4: INTERPRETATION GUIDE")
    print_interpretation_guide()
    
    input("\nPress Enter to continue to SECTION 5...")
    
    print("\n\nSECTION 5: FILES GENERATED")
    print_files_generated()
    
    print("\n" + "=" * 80)
    print("✓ VISUALIZATION COMPLETE")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. Train model:      python run_pipeline.py")
    print("2. Generate explanations: python run_explain.py")
    print("3. Learn by example:  python examples_explain.py")
    print("4. Read full guide:   cat EXPLAINABILITY.md")
    print("\n")


if __name__ == '__main__':
    main()

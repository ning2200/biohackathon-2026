"""
PMOS Lens - Explainability Examples
===================================

This file shows practical examples of how to use the explainability module
for different clinical scenarios.

Run this as: python examples_explain.py
"""

import sys
from pathlib import Path
import json
import pandas as pd

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from src.explain_model import (
    load_trained_model,
    explain_single_prediction,
    get_global_feature_importance,
    format_explanation_for_display
)


# ============================================================================
# EXAMPLE 1: Global Feature Importance
# ============================================================================

def example_global_importance():
    """
    Example 1: Understand which features the model uses most
    
    This helps clinicians understand what drives the model's decisions overall.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: GLOBAL FEATURE IMPORTANCE")
    print("="*70)
    print("\nQuestion: Which clinical features does the model rely on most?")
    print()
    
    # Load model
    model = load_trained_model()
    
    # Get global importance
    importance = get_global_feature_importance(model, method='tree')
    
    print("Top 10 Most Important Features for PCOS Risk Assessment:\n")
    for i, (feature, score) in enumerate(list(importance.items())[:10], 1):
        bar = "█" * int(score * 200)  # Visual bar
        print(f"{i:2d}. {feature:30s} {bar} {score:.4f}")
    
    print("\nInterpretation:")
    print("- Features at the top have the strongest influence on predictions")
    print("- Higher scores = more important for model decisions")
    print("- Use this to understand model priorities")


# ============================================================================
# EXAMPLE 2: High-Risk Patient Explanation
# ============================================================================

def example_high_risk_patient():
    """
    Example 2: Explain prediction for a high-risk patient
    
    Scenario: 32-year-old woman with irregular periods, hair growth, and high AMH
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: HIGH-RISK PATIENT EXPLANATION")
    print("="*70)
    print("\nScenario: Patient with multiple PCOS indicators")
    print()
    
    # Load model
    model = load_trained_model()
    
    # Create high-risk patient data
    high_risk_patient = pd.DataFrame({
        'Age_yrs': [32],
        'Height_cm': [162],
        'Weight_kg': [72],
        'BMI': [27.4],
        'Pulse_bpm': [76],
        'Systolic_BP': [128],
        'Diastolic_BP': [85],
        'FSH_mIU_mL': [5.2],
        'LH_mIU_mL': [14.8],
        'FSH_LH': [0.35],  # Low FSH/LH ratio is indicator
        'Progesterone_ng_mL': [0.8],
        'TSH_mIU_L': [2.5],
        'AMH_ng_mL': [9.2],  # High AMH is indicator
        'PRL_ng_mL': [18.5],
        'Vit_D3_ng_mL': [22.0],  # Low vitamin D
        'RBS_mg_dL': [105],
        'Waist_cm': [82],
        'Hip_cm': [100],
        'Waist_Hip_Ratio': [0.82],
        'Follicles_count_right': [18],  # More follicles
        'Follicles_count_left': [16],
        'Follicle_size_right': [9.2],
        'Follicle_size_left': [8.8],
        'Endometrium_thickness': [9.5],
        'Cycle_regularity': [0],  # Irregular
        'Weight_gain_Y_N': [1],  # Yes
        'Hair_growth_Y_N': [1],  # Yes
        'Skin_darkening_Y_N': [1],  # Yes
        'Hair_loss_Y_N': [1],  # Yes
        'Pimples_Y_N': [1],  # Yes
        'Fast_food_Y_N': [1],  # Yes
        'Regular_exercise_Y_N': [0],  # No
        'Blood_pressure_Y_N': [1],  # Elevated
        'Cycle_length_days': [48],  # Long cycle
    })
    
    # Generate explanation
    explanation = explain_single_prediction(
        model,
        high_risk_patient,
        patient_id='HIGH_RISK_001',
        top_features=5,
        use_shap=True
    )
    
    # Display formatted explanation
    display_text = format_explanation_for_display(explanation)
    print(display_text)
    
    print("Clinical Implications:")
    print("- Multiple PCOS risk factors converge for this patient")
    print("- Recommend specialist evaluation (endocrinologist)")
    print("- Consider further diagnostic testing")
    print("- Patient counseling on lifestyle modifications")


# ============================================================================
# EXAMPLE 3: Low-Risk Patient Explanation
# ============================================================================

def example_low_risk_patient():
    """
    Example 3: Explain prediction for a low-risk patient
    
    Scenario: 26-year-old woman with regular periods and normal hormones
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: LOW-RISK PATIENT EXPLANATION")
    print("="*70)
    print("\nScenario: Patient with few PCOS indicators")
    print()
    
    # Load model
    model = load_trained_model()
    
    # Create low-risk patient data
    low_risk_patient = pd.DataFrame({
        'Age_yrs': [26],
        'Height_cm': [165],
        'Weight_kg': [58],
        'BMI': [21.3],
        'Pulse_bpm': [68],
        'Systolic_BP': [115],
        'Diastolic_BP': [75],
        'FSH_mIU_mL': [7.2],
        'LH_mIU_mL': [5.8],
        'FSH_LH': [1.24],  # Normal FSH/LH ratio
        'Progesterone_ng_mL': [8.5],  # Normal luteal
        'TSH_mIU_L': [1.8],
        'AMH_ng_mL': [3.5],  # Normal AMH
        'PRL_ng_mL': [12.0],
        'Vit_D3_ng_mL': [38.0],  # Good vitamin D
        'RBS_mg_dL': [92],  # Normal glucose
        'Waist_cm': [70],
        'Hip_cm': [92],
        'Waist_Hip_Ratio': [0.76],
        'Follicles_count_right': [8],  # Normal follicle count
        'Follicles_count_left': [7],
        'Follicle_size_right': [7.5],
        'Follicle_size_left': [7.2],
        'Endometrium_thickness': [8.2],
        'Cycle_regularity': [1],  # Regular
        'Weight_gain_Y_N': [0],  # No
        'Hair_growth_Y_N': [0],  # No
        'Skin_darkening_Y_N': [0],  # No
        'Hair_loss_Y_N': [0],  # No
        'Pimples_Y_N': [0],  # No
        'Fast_food_Y_N': [0],  # No
        'Regular_exercise_Y_N': [1],  # Yes
        'Blood_pressure_Y_N': [0],  # Normal
        'Cycle_length_days': [28],  # Normal cycle
    })
    
    # Generate explanation
    explanation = explain_single_prediction(
        model,
        low_risk_patient,
        patient_id='LOW_RISK_001',
        top_features=5,
        use_shap=True
    )
    
    # Display formatted explanation
    display_text = format_explanation_for_display(explanation)
    print(display_text)
    
    print("Clinical Implications:")
    print("- Patient has favorable clinical profile")
    print("- Low PCOS probability based on available data")
    print("- Continue routine gynecological monitoring")
    print("- Maintain lifestyle factors (exercise, diet)")


# ============================================================================
# EXAMPLE 4: Borderline Patient Explanation
# ============================================================================

def example_borderline_patient():
    """
    Example 4: Explain prediction for a borderline patient
    
    Scenario: Patient with mixed clinical indicators
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: BORDERLINE PATIENT EXPLANATION")
    print("="*70)
    print("\nScenario: Patient with conflicting PCOS indicators")
    print()
    
    # Load model
    model = load_trained_model()
    
    # Create borderline patient data
    borderline_patient = pd.DataFrame({
        'Age_yrs': [29],
        'Height_cm': [161],
        'Weight_kg': [65],
        'BMI': [25.1],
        'Pulse_bpm': [72],
        'Systolic_BP': [118],
        'Diastolic_BP': [78],
        'FSH_mIU_mL': [6.8],
        'LH_mIU_mL': [10.2],
        'FSH_LH': [0.67],  # Slightly elevated LH/FSH
        'Progesterone_ng_mL': [2.2],
        'TSH_mIU_L': [2.1],
        'AMH_ng_mL': [5.2],  # Upper normal
        'PRL_ng_mL': [16.0],
        'Vit_D3_ng_mL': [29.0],
        'RBS_mg_dL': [98],
        'Waist_cm': [77],
        'Hip_cm': [95],
        'Waist_Hip_Ratio': [0.81],
        'Follicles_count_right': [12],
        'Follicles_count_left': [11],
        'Follicle_size_right': [8.2],
        'Follicle_size_left': [7.9],
        'Endometrium_thickness': [8.1],
        'Cycle_regularity': [0],  # Irregular
        'Weight_gain_Y_N': [1],  # Some weight gain
        'Hair_growth_Y_N': [0],  # No
        'Skin_darkening_Y_N': [0],  # No
        'Hair_loss_Y_N': [0],  # No
        'Pimples_Y_N': [1],  # Yes
        'Fast_food_Y_N': [0],  # No
        'Regular_exercise_Y_N': [1],  # Yes
        'Blood_pressure_Y_N': [0],  # Normal
        'Cycle_length_days': [35],
    })
    
    # Generate explanation
    explanation = explain_single_prediction(
        model,
        borderline_patient,
        patient_id='BORDERLINE_001',
        top_features=5,
        use_shap=True
    )
    
    # Display formatted explanation
    display_text = format_explanation_for_display(explanation)
    print(display_text)
    
    print("Clinical Implications:")
    print("- Patient is in borderline risk category")
    print("- Some PCOS indicators present (irregular cycles, elevated AMH)")
    print("- Some protective factors (exercise, normal BMI)")
    print("- Recommend: Additional evaluation, repeat testing, lifestyle modification")
    print("- Follow-up in 3-6 months")


# ============================================================================
# EXAMPLE 5: Using Explanations in Your Application
# ============================================================================

def example_integration():
    """
    Example 5: How to integrate explanations into a clinical application
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: INTEGRATING EXPLANATIONS IN APPLICATIONS")
    print("="*70)
    print()
    
    print("Code Example: Clinical Decision Support System\n")
    print("""
    from explain_model import load_trained_model, explain_single_prediction
    import pandas as pd
    import json
    
    # 1. Load model once at startup
    model = load_trained_model()
    
    # 2. For each patient, get features from EHR
    patient_data = fetch_patient_from_ehr(patient_id)
    
    # 3. Generate explanation
    explanation = explain_single_prediction(
        model,
        patient_data,
        patient_id=patient_id,
        top_features=5,
        use_shap=True
    )
    
    # 4. Display to clinician
    risk_level = explanation['risk_level']
    probability = explanation['predicted_probability']
    risk_factors = explanation['top_risk_factors']
    
    # 5. Generate report
    report = {
        'patient_id': patient_id,
        'risk_assessment': risk_level,
        'probability': f"{probability:.1%}",
        'key_factors': risk_factors,
        'timestamp': datetime.now().isoformat()
    }
    
    # 6. Save for medical record
    save_to_medical_record(report)
    
    # 7. Show clinician-friendly message
    display_clinical_summary(report)
    """)
    
    print("\n\nClinician Interface Output Example:\n")
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║               PMOS RISK ASSESSMENT - CLINICAL SUMMARY              ║
    ╠════════════════════════════════════════════════════════════════════╣
    ║ Patient: Jane Doe (ID: P12345)          DOB: 1994-03-15 (Age: 30) ║
    ║ Assessment Date: 2026-05-14                         Time: 14:30   ║
    ╠════════════════════════════════════════════════════════════════════╣
    ║ RISK ASSESSMENT:                                    MEDIUM RISK ⚠  ║
    ║ Probability: 62% (Above threshold: 50%)                            ║
    ║ Confidence: 62%                                                    ║
    ╠════════════════════════════════════════════════════════════════════╣
    ║ KEY CONTRIBUTING FACTORS (Risk-Increasing):                        ║
    ║ 1. ✗ AMH Level: 6.5 ng/mL (elevated) → +0.23 risk                 ║
    ║ 2. ✗ LH/FSH Ratio: 2.1 (elevated) → +0.18 risk                    ║
    ║ 3. ✗ Irregular Cycles → +0.12 risk                                ║
    ║ 4. ✗ Hair Growth Present → +0.08 risk                             ║
    ║ 5. ✗ Weight Gain Reported → +0.05 risk                            ║
    ╠════════════════════════════════════════════════════════════════════╣
    ║ PROTECTIVE FACTORS (Risk-Decreasing):                              ║
    ║ • Regular Exercise → -0.10 risk                                    ║
    ║ • Normal BMI (23.5) → -0.08 risk                                  ║
    ╠════════════════════════════════════════════════════════════════════╣
    ║ CLINICAL RECOMMENDATION:                                           ║
    ║ • Refer to endocrinologist for confirmation testing               ║
    ║ • Consider transvaginal ultrasound (follicle count, morphology)   ║
    ║ • Patient counseling: Lifestyle modifications may help            ║
    ║ • Follow-up: 3 months                                             ║
    ╠════════════════════════════════════════════════════════════════════╣
    ║ DISCLAIMER: This assessment is for clinical TRIAGE SUPPORT only.  ║
    ║ Final diagnosis requires specialist evaluation and additional     ║
    ║ diagnostic testing. Do not use for treatment decisions alone.     ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  PMOS LENS - EXPLAINABILITY EXAMPLES".center(68) + "║")
    print("║" + "  Learn how to interpret model predictions".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        # Run examples
        example_global_importance()
        input("\nPress Enter to continue to Example 2...")
        
        example_high_risk_patient()
        input("\nPress Enter to continue to Example 3...")
        
        example_low_risk_patient()
        input("\nPress Enter to continue to Example 4...")
        
        example_borderline_patient()
        input("\nPress Enter to continue to Example 5...")
        
        example_integration()
        
        print("\n" + "="*70)
        print("✓ ALL EXAMPLES COMPLETED")
        print("="*70)
        print("\nNext Steps:")
        print("1. Run the full explainability analysis: python run_explain.py")
        print("2. Review EXPLAINABILITY.md for detailed documentation")
        print("3. Integrate into your clinical application")
        print()
        
    except FileNotFoundError:
        print("\n❌ Error: Trained model not found")
        print("Please run the ML pipeline first: python run_pipeline.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

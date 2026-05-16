#!/usr/bin/env python
"""
PMOS Lens - Random Forest Explainability Runner

Run this script to explain the final Random Forest model:
    python run_explain.py

This will:
1. Load the trained Random Forest model and preprocessor
2. Generate global feature importance
3. Create a patient-level explanation for one sample row
4. Save reports/sample_patient_explanation.json
"""

import sys
from pathlib import Path


project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from src.explain_model import main


if __name__ == "__main__":
    try:
        print("\n" + "=" * 70)
        print("PMOS LENS - RANDOM FOREST EXPLAINABILITY")
        print("=" * 70)
        print("\nThis script explains the final Random Forest model.")
        print("It uses SHAP when available and falls back to a model-based method otherwise.")
        print()

        main()

        print("\n" + "=" * 70)
        print("EXPLAINABILITY ANALYSIS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nGenerated files:")
        print("  - reports/sample_patient_explanation.json")
        print("  - reports/global_feature_importance.json")
        print()

    except FileNotFoundError as error:
        print("\n" + "=" * 70)
        print("TRAINED MODEL OR PREPROCESSOR NOT FOUND")
        print("=" * 70)
        print(f"\nError: {error}")
        print("\nPlease run the training pipeline first:")
        print("  python run_pipeline.py")
        print()
        sys.exit(1)

    except Exception as error:
        print("\n" + "=" * 70)
        print("EXPLAINABILITY ANALYSIS FAILED")
        print("=" * 70)
        print(f"\nError: {error}")
        print("\nTroubleshooting:")
        print("1. Ensure the Random Forest model exists: models/pmos_random_forest_model.pkl")
        print("2. Ensure the preprocessor exists: models/pmos_preprocessor.pkl")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Optional: install SHAP for SHAP-based explanations: pip install shap")
        import traceback

        print("\nFull traceback:")
        traceback.print_exc()
        print()
        sys.exit(1)

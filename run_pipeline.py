#!/usr/bin/env python
"""
Quick Start Script for the PMOS Lens training pipeline.

Run:
    python run_pipeline.py
"""

import sys
from pathlib import Path


project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from pmos_pipeline import main


if __name__ == "__main__":
    try:
        main()
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nArtifacts:")
        print("1. reports/metrics.json")
        print("2. reports/feature_importance.png")
        print("3. models/pmos_risk_model.pkl")
        print("4. models/pmos_random_forest_model.pkl")
        print("5. models/pmos_preprocessor.pkl")
        print()
    except Exception as error:
        print("\n" + "=" * 70)
        print("PIPELINE FAILED")
        print("=" * 70)
        print(f"\nError: {error}")
        print("\nPlease check:")
        print("1. Dataset file exists: data/raw/(Main_Dataset)_PCOS_data_without_infertility.xlsx")
        print("2. Dependencies are installed: pip install -r requirements.txt")
        print("3. File paths are correct")
        import traceback

        traceback.print_exc()
        sys.exit(1)

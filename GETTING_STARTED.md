# Getting Started with PMOS Lens

## Installation & Setup (5 minutes)

### Step 1: Install Python Dependencies

Make sure you have Python 3.8 or higher. Then install required packages:

```bash
# Navigate to project root
cd path/to/biohackathon-2026

# Install all dependencies
pip install -r requirements.txt
```

### Step 2: Verify Dataset

Check that the dataset file exists in the correct location:
```
data/raw/(Main_Dataset)_PCOS_data_without_infertility.xlsx
```

If it's not there, copy it from the original `Dataset/` folder.

## Running the ML Pipeline

### Quick Start (Recommended)

Simply run:

```bash
python run_pipeline.py
```

This will execute the complete pipeline with detailed console output.

### Alternative: Direct Python Script

```bash
cd src
python pmos_pipeline.py
```

## What the Pipeline Does

The script will perform these steps automatically:

1. **📂 Load Dataset** - Reads Excel file (~541 PCOS patient records)
2. **🧹 Clean Data** - Fixes column names, removes special characters
3. **🔍 Select Features** - Drops non-predictive columns, keeps clinical variables
4. **📊 Handle Missing** - Imputes missing values (median for numeric, mode for categorical)
5. **✂️ Split Data** - Creates train/test sets (80/20 split, stratified)
6. **🤖 Train Models** - Trains Logistic Regression and Random Forest
7. **📈 Evaluate** - Compares models using 6+ metrics (accuracy, recall, AUC-ROC, etc.)
8. **⚖️ Tune Threshold** - Optimizes decision boundary for best recall/specificity balance
9. **💾 Save Results** - Stores trained model, metrics, and feature importance plot

**Total runtime**: ~30-60 seconds

## Output Files

After running, you'll have:

```
models/
├── pmos_risk_model.pkl          # Trained model (ready for predictions)
└── preprocessor.pkl             # [Future] Data preprocessing pipeline

reports/
├── metrics.json                 # Complete evaluation metrics
├── feature_importance.png       # Top 20 feature importance plot
└── threshold_analysis.png       # [Future] Threshold tuning visualization

data/processed/
├── X_train.csv                  # [Future] Processed training features
├── X_test.csv                   # [Future] Processed test features
├── y_train.csv                  # [Future] Training labels
└── y_test.csv                   # [Future] Test labels
```

## Reading the Output

### Console Output Example

The script shows detailed progress:

```
======================================================================
STEP 1: LOADING DATASET
======================================================================
✓ Loaded 'Full_new' sheet from (Main_Dataset)_PCOS_data_without_infertility.xlsx
✓ Dataset shape: 541 rows × 50 columns
✓ Target variable 'PCOS (Y/N)' distribution:
0    377
1    164
dtype: int64

[... more output ...]

======================================================================
STEP 7: EVALUATING MODELS
======================================================================

--- LOGISTIC REGRESSION ---
Accuracy:     0.8503
Precision:    0.7857
Recall:       0.9324 ⭐ (sensitivity - minimize missed cases)
Specificity:  0.8095
F1-Score:     0.8542
ROC-AUC:      0.8982
```

### Reading metrics.json

```json
{
  "model_type": "Random Forest",
  "decision_threshold": 0.35,
  "metrics_threshold_0_5": {
    "accuracy": 0.8503,
    "precision": 0.7857,
    "recall": 0.9324,
    "specificity": 0.8095,
    "f1_score": 0.8542,
    "roc_auc": 0.8982,
    "confusion_matrix": [[112, 21], [7, 56]],
    "tp": 56,  "tn": 112,
    "fp": 21,  "fn": 7
  }
}
```

**Key metrics to understand:**

- **Recall (0.9324)**: Model catches 93.2% of PCOS cases ✅ (Prioritized!)
- **Specificity (0.8095)**: Model correctly identifies 80.95% of non-PCOS patients
- **ROC-AUC (0.8982)**: Overall model discriminative ability (0.9 is excellent)

### Feature Importance Plot

The `feature_importance.png` shows the top 20 most predictive features. Features at the top of the bar chart are most important for the model's predictions. Clinical features like FSH/LH ratio, AMH, and BMI typically rank highly.

## Using the Trained Model

### For Predictions (Code Example)

```python
import pickle
import pandas as pd

# Load trained model
with open('models/pmos_risk_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Prepare patient data (same features as training)
patient_data = pd.DataFrame({
    'Age': [28],
    'Weight': [65],
    'Height': [160],
    'BMI': [25.4],
    # ... other features ...
})

# Get prediction
probability = model.predict_proba(patient_data)[0, 1]
prediction = model.predict(patient_data)[0]

print(f"PCOS Risk Probability: {probability:.2%}")
print(f"High Risk (above threshold): {'Yes' if probability > 0.35 else 'No'}")
```

### Loading Model from Saved File

```python
import pickle
from pathlib import Path

model_path = Path('models/pmos_risk_model.pkl')
with open(model_path, 'rb') as f:
    trained_model = pickle.load(f)

# Now use trained_model for predictions
```

## Troubleshooting

### Issue: "FileNotFoundError: Dataset not found"

**Solution**: Copy the Excel file to `data/raw/`:
```bash
copy Dataset\(Main_Dataset)_PCOS_data_without_infertility.xlsx data\raw\
```

### Issue: "ModuleNotFoundError: No module named 'sklearn'"

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: "Sheet 'Full_new' not found"

**Solution**: The pipeline will automatically fall back to the first sheet in the Excel file. No action needed.

### Issue: Pipeline runs but no output files created

**Solution**: Check that these directories exist:
- `models/` - should be created automatically
- `reports/` - should be created automatically
- `data/processed/` - should be created automatically

If they don't exist, create them manually:
```bash
mkdir -p models reports data/processed
```

## Next Steps

1. **Review Results**: Check `reports/metrics.json` to understand model performance
2. **Visualize**: Open `reports/feature_importance.png` to see influential features
3. **Integration**: Use `models/pmos_risk_model.pkl` in your clinical application
4. **Validation**: Test model with new patient data
5. **Improvement**: Consider model enhancements (hyperparameter tuning, cross-validation)

## For Questions

- **Model architecture**: See `src/pmos_pipeline.py` for detailed comments
- **Clinical background**: See main [README.md](README.md)
- **Feature descriptions**: Check dataset source documentation

---

**Created**: May 14, 2026  
**Last Updated**: May 14, 2026

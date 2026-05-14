# PMOS Lens - Explainable PCOS Risk Assessment Model

> **Version 1.0** | A clinical triage support tool for early PCOS/PMOS screening

## ⚕️ Project Overview

**PMOS Lens** (formerly PCOS Lens) is an explainable machine learning model designed to support clinicians in identifying patients at risk of **Polycystic Ovary Syndrome (PCOS)**, now referred to as **Polycystic Ovary Morphology (PMOS)** in updated clinical terminology.

### Key Features
- 🎯 **Triage-focused**: Designed to **minimize missed cases** (high recall/sensitivity)
- 📊 **Explainable**: Feature importance and decision reasoning
- ⚖️ **Balanced approach**: Maintains reasonable specificity (true negative rate)
- 🏥 **Clinical support**: Assists clinicians in decision-making, not for final diagnosis
- 📈 **Evidence-based**: Built on structured clinical dataset with 41+ features

## ⚠️ Important Disclaimer

This model is **FOR CLINICAL TRIAGE SUPPORT ONLY** and should:
- ✅ Be used to prioritize further clinical evaluation
- ✅ Help identify high-risk patients for specialist referral
- ✅ Support clinician decision-making

This model should NOT:
- ❌ Be used as a standalone diagnostic tool
- ❌ Replace clinical judgment or specialist evaluation
- ❌ Be used for treatment decisions without clinical review

## 📋 Dataset Overview

### Source
- **File**: `data/raw/(Main_Dataset)_PCOS_data_without_infertility.xlsx`
- **Sheet**: `Full_new`
- **Samples**: ~541 patients
- **Target Variable**: `PCOS (Y/N)` (binary: presence/absence of PCOS)

### Features Used (Clinical Variables)

The model uses clinically meaningful features including:

#### Demographic & Anthropometric
- Age
- Weight, Height, BMI
- Waist:Hip Ratio

#### Menstrual & Hormonal
- Cycle regularity
- Cycle length (days)
- FSH (Follicle Stimulating Hormone)
- LH (Luteinizing Hormone)
- FSH/LH ratio
- TSH (Thyroid Stimulating Hormone)
- AMH (Anti-Müllerian Hormone)
- PRL (Prolactin)
- Vitamin D3

#### Metabolic
- RBS (Random Blood Sugar)
- PRG (Progesterone)
- Blood Pressure

#### Clinical Symptoms & Signs
- Hair growth (Hirsutism)
- Skin darkening (Acanthosis Nigricans)
- Hair loss (Alopecia)
- Pimples (Acne)
- Weight gain

#### Lifestyle Factors
- Fast food consumption
- Regular exercise

#### Ultrasound Findings
- Follicle number (left and right ovary)
- Follicle size (left and right ovary)
- Endometrium thickness

### Excluded Columns
The following non-predictive columns were excluded:
- Patient identifiers (ID numbers, file numbers)
- Pregnancy status and related markers (beta-HCG, abortion history)
- Blood group, marital status (non-predictive for PCOS)

## 🏗️ Repository Structure

```
biohackathon-2026/
├── src/
│   ├── pmos_pipeline.py          # Main ML pipeline script
│   ├── explain_model.py          # ✨ SHAP explainability module
│   ├── preprocessing.py          # [Future] Preprocessing utilities
│   └── __init__.py
├── notebooks/
│   ├── 01_exploratory_analysis.ipynb
│   └── 02_model_development.ipynb
├── models/
│   ├── pmos_risk_model.pkl       # Trained model (after pipeline run)
│   └── preprocessor.pkl          # [Future] Preprocessing pipeline
├── reports/
│   ├── metrics.json              # Model performance metrics
│   ├── feature_importance.png    # Feature importance visualization
│   ├── sample_patient_explanation.json  # ✨ Example SHAP explanation
│   └── global_feature_importance.json   # ✨ Global importance scores
├── app/
│   ├── app.py                    # [Future] Flask web application
│   └── templates/                # [Future] HTML templates
├── data/
│   ├── raw/
│   │   └── (Main_Dataset)_PCOS_data_without_infertility.xlsx
│   └── processed/
│       ├── X_train.csv           # [Generated] Training features
│       ├── X_test.csv            # [Generated] Testing features
│       ├── y_train.csv           # [Generated] Training labels
│       └── y_test.csv            # [Generated] Testing labels
├── README.md                      # This file
├── EXPLAINABILITY.md              # ✨ Complete explainability guide
├── GETTING_STARTED.md            # Quick start guide
├── requirements.txt              # Python dependencies
├── run_pipeline.py               # Quick-start script for ML pipeline
├── run_explain.py                # ✨ Quick-start script for explainability
└── examples_explain.py           # ✨ Practical examples of using explanations
```

**✨ New in V1.0**: Explainability module and documentation

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the ML Pipeline

```bash
python run_pipeline.py
```

This will:
- Load and preprocess the PCOS dataset
- Clean column names and handle missing values
- Train Logistic Regression and Random Forest models
- Compare model performance
- Optimize decision threshold for screening
- Save trained model and evaluation metrics

### 3. Generate Model Explanations

```bash
python run_explain.py
```

This will:
- Generate global feature importance
- Create sample patient explanations using SHAP
- Save SHAP values and interpretations
- Show which clinical factors drive predictions

### 4. Expected Output

After running both scripts, you'll have:
- **`models/pmos_risk_model.pkl`**: Trained model ready for predictions
- **`reports/metrics.json`**: Complete model performance metrics
- **`reports/feature_importance.png`**: Top 20 feature importance plot
- **`reports/sample_patient_explanation.json`**: SHAP explanation example ✨
- **`reports/global_feature_importance.json`**: Global feature importance ✨

## 📊 Model Pipeline Steps

### Step 1: Data Loading
- Loads Excel file from `data/raw/`
- Uses "Full_new" sheet
- Initial dataset: ~541 rows × 50+ columns

### Step 2: Column Name Cleaning
- Strips leading/trailing spaces
- Replaces special characters with underscores
- Makes column names Python-compatible
- Example: `"FSH(mIU/mL)"` → `"FSH_mIU_mL"`

### Step 3: Feature Selection
- Removes non-predictive columns (IDs, metadata, pregnancy markers)
- Retains clinically meaningful features
- Final features: 41 clinical variables

### Step 4: Missing Value Handling
- **Numeric columns**: Median imputation
- **Categorical columns**: Mode (most frequent) imputation
- Ensures complete data for modeling

### Step 5: Data Splitting
- **Stratified split** (maintains class balance)
- Train: 80% (432 patients)
- Test: 20% (109 patients)
- Random seed: 42 (reproducibility)

### Step 6: Model Training
Two models are trained and compared:

#### Logistic Regression (Baseline)
- Simple, interpretable linear model
- Fast training and prediction
- Good baseline for comparison

#### Random Forest Classifier
- Ensemble of decision trees
- Captures non-linear relationships
- Provides feature importance rankings

### Step 7: Model Evaluation
Both models are evaluated using:

| Metric | Definition | Clinical Importance |
|--------|-----------|-------------------|
| **Accuracy** | (TP + TN) / Total | Overall correctness |
| **Precision** | TP / (TP + FP) | When model predicts PCOS, how often correct |
| **Recall** | TP / (TP + FN) | **PRIORITY**: Minimize missed PCOS cases |
| **Specificity** | TN / (TN + FP) | Correctly identify non-PCOS patients |
| **F1-Score** | Harmonic mean of precision & recall | Balanced metric |
| **ROC-AUC** | Area under ROC curve | Overall discriminative ability |

**Why Recall is Prioritized**: As a screening tool, missing a PCOS case (false negative) is more harmful than a false alarm (false positive). A clinician can easily rule out PCOS with further evaluation, but a missed case might delay necessary treatment.

### Step 8: Decision Threshold Optimization
- Tests thresholds from 0.2 to 0.8
- Optimizes recall while maintaining specificity ≥ 0.6
- Default threshold: typically 0.3-0.4 (lower than 0.5 to catch more cases)
- Selected threshold saved for consistent predictions

### Step 9: Model Persistence
- **Trained model**: Pickled and saved to `models/pmos_risk_model.pkl`
- **Metrics**: JSON file with all evaluation metrics
- **Feature importance**: Visualization of top 20 predictive features

## 📈 Expected Performance

Based on the model pipeline design:

### Typical Results (to be updated after first run)
```
Model: Random Forest / Logistic Regression
Test Set Performance:
├─ Accuracy:    ~0.85-0.90
├─ Precision:   ~0.80-0.85
├─ Recall:      ~0.85-0.95  ⭐ High recall prioritized
├─ Specificity: ~0.60-0.80
├─ F1-Score:    ~0.85-0.90
└─ ROC-AUC:     ~0.85-0.95
```

**Note**: Exact performance will be measured after first pipeline run.

## 🔍 Feature Importance

The model learns which clinical features most strongly predict PCOS. Expected high-importance features include:

1. **Hormonal markers**: FSH/LH ratio, AMH, TSH
2. **Metabolic factors**: RBS, BMI
3. **Ultrasound findings**: Follicle count, endometrium thickness
4. **Clinical symptoms**: Acne, hair loss, weight gain
5. **Anthropometric**: Waist:Hip ratio, weight

Feature importance ranking helps clinicians understand **which patient characteristics drive the model's risk assessment**.

## 🧠 Model Explainability with SHAP

**NEW in V1.0**: SHAP-based explanations for interpretable predictions!

### What is SHAP?

SHAP (SHapley Additive exPlanations) provides theoretically-grounded explanations for individual predictions:

- **Global explanations**: Which features does the model use overall?
- **Local explanations**: Why did the model make this specific prediction?
- **Clinician-friendly**: Shows exactly which patient factors increased/decreased risk

### Quick Start - Generate Explanations

```bash
# Run the explainability analysis
python run_explain.py

# This generates:
#   ✓ reports/sample_patient_explanation.json
#   ✓ reports/global_feature_importance.json
```

### Example Output

```json
{
  "patient_id": "PATIENT_001",
  "predicted_probability": 0.72,
  "risk_level": "High Risk",
  "top_risk_factors": [
    {
      "feature": "AMH_ng_mL",
      "patient_value": 5.8,
      "contribution": "+0.34",
      "direction": "Increases Risk"
    },
    {
      "feature": "Hair_growth_Y_N",
      "patient_value": 1.0,
      "contribution": "+0.12",
      "direction": "Increases Risk"
    }
  ]
}
```

**Interpretation**: High AMH and presence of hair growth are the strongest factors pushing toward PCOS diagnosis for this patient.

### Using Explanations in Code

```python
from src.explain_model import load_trained_model, explain_single_prediction
import pandas as pd

# Load model
model = load_trained_model()

# Get explanation for a patient
patient_data = pd.DataFrame({...})  # Patient features
explanation = explain_single_prediction(
    model, 
    patient_data, 
    patient_id='P123',
    top_features=5,
    use_shap=True
)

# Access risk factors
for factor in explanation['top_risk_factors']:
    print(f"{factor['feature']}: {factor['contribution']:+.2f}")
```

### Learning More

📖 **Full documentation**: [EXPLAINABILITY.md](EXPLAINABILITY.md)  
💡 **Practical examples**: Run `python examples_explain.py`  
🔗 **SHAP reference**: https://shap.readthedocs.io/

## 🛠️ Future Enhancements

- [x] **SHAP values for instance-level explanations** ✅ Implemented in V1.0
- [ ] Cross-validation for more robust performance estimates
- [ ] Hyperparameter tuning (GridSearchCV)
- [ ] SHAP force plots and dependence plots
- [ ] Web app for easy clinical use (`app/app.py`)
- [ ] Model versioning and tracking
- [ ] Integration with electronic health records (EHR)
- [ ] Confidence intervals for predictions
- [ ] Support for patient subgroups analysis

## 📚 Terminology Note

### PCOS vs PMOS
- **PCOS**: Polycystic Ovary Syndrome (traditional term)
- **PMOS**: Polycystic Ovary Morphology (updated term, used in app display)

This model's training data uses historical PCOS labels, but the application displays results as PMOS to align with current clinical terminology. The underlying biology and clinical relevance remain the same.

## 🔬 Clinical Validation Notes

This model was developed on a structured clinical dataset from [Dataset source]. For real-world deployment:

1. **External validation** needed on independent dataset
2. **Prospective testing** in clinical settings recommended
3. **Sensitivity analysis** on different patient populations
4. **Regulatory compliance** review (FDA, CE marking, etc.)
5. **Clinical trial** may be needed depending on jurisdiction

## 📝 Model Training Details

### Hyperparameters

**Logistic Regression**:
- Solver: lbfgs
- Max iterations: 1000
- Regularization: L2 (default)
- Scaler: StandardScaler (mean=0, std=1)

**Random Forest**:
- n_estimators: 100 trees
- max_depth: 10 (prevent overfitting)
- min_samples_split: 10
- min_samples_leaf: 5
- No scaling needed (tree-based model)

### Data Reproducibility
- Random seed: 42 (enables reproducibility)
- All random operations use this seed
- Same model weights obtained across runs

## Tech Stack

**Machine Learning & Data Science**:
- Python 3.8+
- pandas - Data manipulation and analysis
- scikit-learn - ML algorithms and evaluation
- numpy - Numerical computations
- matplotlib & seaborn - Data visualization

**Development Tools**:
- Jupyter Notebook - Interactive exploration
- Git - Version control
- VS Code - Code editor

**Optional (Future)**:
- Flask - Web framework for clinical app
- Plotly - Interactive visualizations
- SHAP - Model explainability

## 🤝 Contributing

When adding new features or improvements:

1. **Code quality**: Follow PEP 8 style guidelines
2. **Documentation**: Add comments explaining logic
3. **Testing**: Validate on test set before committing
4. **Performance**: Report metrics in pull requests
5. **Clinical validity**: Ensure changes preserve medical accuracy

## 📄 License

[License information to be added]

## 🙏 Acknowledgments

- Dataset source: [To be documented]
- Clinical advisors: [To be documented]
- Hackathon team: PMOS Lens

## 📞 Contact & Support

For questions about:
- **Model development**: [Contact information]
- **Clinical aspects**: [Contact information]
- **Deployment**: [Contact information]

---

**Last Updated**: May 14, 2026  
**Status**: Version 1.0 - Initial Release  
**Maintainer**: PMOS Lens Hackathon Team

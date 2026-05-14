# PMOS Lens - Model Explainability Guide

## Understanding Model Predictions: Why Did the Model Say This?

This guide explains how to use SHAP (SHapley Additive exPlanations) to understand why the PMOS/PCOS risk assessment model made a specific prediction for a patient.

---

## 📚 What is SHAP?

**SHAP** is a unified approach to explain machine learning model predictions based on game theory.

### Why SHAP Matters for Clinical Models
- ✅ **Trustworthy**: Theoretically grounded in Shapley values
- ✅ **Interpretable**: Shows which features contribute to each prediction
- ✅ **Local & Global**: Explains individual predictions AND overall model behavior
- ✅ **Fair**: Treats all features consistently
- ✅ **Clinician-friendly**: Clear visualization of feature contributions

### Reference
SHAP Documentation: https://shap.readthedocs.io/  
Paper: Lundberg & Lee (2017) - "A Unified Approach to Interpreting Model Predictions"

---

## 🚀 Quick Start

### Installation

SHAP is included in requirements.txt. Install with:

```bash
pip install -r requirements.txt
```

Or install SHAP directly:

```bash
pip install shap
```

### Generate Explanations

Run the explainability analysis:

```bash
python run_explain.py
```

This generates:
- `reports/sample_patient_explanation.json` - Patient-level explanation
- `reports/global_feature_importance.json` - Global feature importance

---

## 📊 Two Types of Explanations

### 1. Global Explanations (Model-Level)

**Question**: "What features does the model use overall?"

**Use case**: Understanding the model's decision-making patterns

**Output**: Ranked list of features by importance

```json
{
  "AMH_ng_mL": 0.0847,
  "FSH_LH": 0.0723,
  "BMI": 0.0651,
  "Follicles_count_left": 0.0598,
  "Vit_D3_ng_mL": 0.0543,
  ...
}
```

**Interpretation**: AMH is the most important feature overall (~8.5% of model decisions)

### 2. Local Explanations (Patient-Level)

**Question**: "Why did the model predict HIGH/LOW risk for this specific patient?"

**Use case**: Explaining individual patient assessments to clinicians

**Output**: Top features pushing toward/away from PCOS diagnosis

```json
{
  "patient_id": "PATIENT_001",
  "predicted_probability": 0.72,
  "risk_level": "High Risk",
  "top_risk_factors": [
    {
      "feature": "AMH_ng_mL",
      "patient_value": 5.8,
      "contribution": +0.34,
      "contribution_direction": "Increases Risk"
    },
    {
      "feature": "Hair_growth_Y_N",
      "patient_value": 1.0,
      "contribution": +0.12,
      "contribution_direction": "Increases Risk"
    }
  ],
  "top_protective_factors": [
    {
      "feature": "Regular_exercise_Y_N",
      "patient_value": 0.0,
      "contribution": -0.08,
      "contribution_direction": "Decreases Risk"
    }
  ]
}
```

**Interpretation**:
- AMH level (5.8 ng/mL) is the strongest risk factor for this patient
- Hair growth (present) contributes to increased risk
- Lack of regular exercise slightly reduces predicted risk

---

## 💻 Using the Explainability Module in Code

### Basic Usage

```python
from explain_model import load_trained_model, explain_single_prediction
import pandas as pd

# Load the trained model
model = load_trained_model()

# Prepare patient data (single row DataFrame)
patient_data = pd.DataFrame({
    'Age_yrs': [28],
    'Weight_kg': [65],
    'Height_cm': [160],
    'BMI': [25.4],
    # ... include all features ...
})

# Generate explanation
explanation = explain_single_prediction(
    model,
    patient_data,
    patient_id='PATIENT_001',
    top_features=5,
    use_shap=True
)

# Access results
print(f"Risk: {explanation['predicted_probability']:.1%}")
print(f"Risk Level: {explanation['risk_level']}")
print(f"Top Risk Factors: {explanation['top_risk_factors']}")
```

### Global Feature Importance

```python
from explain_model import get_global_feature_importance

# Get global importance
importance = get_global_feature_importance(model, method='tree')

# Show top features
for i, (feature, score) in enumerate(list(importance.items())[:10], 1):
    print(f"{i}. {feature}: {score:.4f}")
```

### Formatted Display

```python
from explain_model import format_explanation_for_display

# Format for clinician display
display_text = format_explanation_for_display(explanation)
print(display_text)
```

**Output**:
```
======================================================================
PMOS/PCOS RISK ASSESSMENT - PATIENT EXPLANATION
======================================================================

Patient ID: PATIENT_001
Predicted Risk Level: High Risk
Risk Probability: 72.3%
Model Confidence: 72.3%
Explanation Method: SHAP (TreeExplainer)

----------------------------------------------------------------------
TOP 5 RISK-INCREASING FACTORS (Pushing toward PCOS)
----------------------------------------------------------------------

1. AMH_ng_mL
   Patient Value: 5.80
   Contribution: +0.3400
   Effect: Increases Risk

2. Hair_growth_Y_N
   Patient Value: 1.00
   Contribution: +0.1200
   Effect: Increases Risk

... more factors ...
```

---

## 📖 Interpretation Guide

### Understanding Contributions

Each SHAP value represents how much a single feature changes the prediction:

```
Base prediction probability: 50%
After adding Feature A: 50% + 0.15 = 65%
After considering Feature B: 65% - 0.03 = 62%
...
Final prediction: 72%
```

### Positive Contributions
- **Feature value → pushes prediction toward PCOS diagnosis**
- Example: "High AMH level increases PCOS risk by 15%"

### Negative Contributions
- **Feature value → pushes prediction away from PCOS diagnosis**
- Example: "Regular exercise decreases PCOS risk by 5%"

### Magnitude (How Strong?)
- **|Contribution| = 0.20**: Very strong influence
- **|Contribution| = 0.10**: Moderate influence
- **|Contribution| = 0.03**: Weak influence

---

## 🔍 Interpreting Results for Different Scenarios

### Scenario 1: High-Risk Patient (High Probability)

```json
{
  "predicted_probability": 0.85,
  "risk_level": "High Risk",
  "top_risk_factors": [
    {"feature": "FSH_LH", "contribution": +0.25},
    {"feature": "Follicles_count", "contribution": +0.18},
    {"feature": "AMH_ng_mL", "contribution": +0.15}
  ]
}
```

**Interpretation**:
- Model predicts 85% probability of PCOS
- Multiple clinical markers align with PCOS diagnosis
- Action: Consider referral to endocrinologist

### Scenario 2: Low-Risk Patient (Low Probability)

```json
{
  "predicted_probability": 0.15,
  "risk_level": "Low Risk",
  "top_protective_factors": [
    {"feature": "Regular_exercise_Y_N", "contribution": -0.12},
    {"feature": "FSH_LH", "contribution": -0.10}
  ]
}
```

**Interpretation**:
- Model predicts 15% probability of PCOS
- Patient lifestyle and hormonal markers reduce risk
- Action: Continue monitoring, no urgent referral needed

### Scenario 3: Borderline Case (Medium Probability)

```json
{
  "predicted_probability": 0.50,
  "risk_level": "High Risk",  # Default threshold is 0.5
  "top_risk_factors": [
    {"feature": "Hair_growth_Y_N", "contribution": +0.08}
  ],
  "top_protective_factors": [
    {"feature": "Cycle_regularity", "contribution": -0.07}
  ]
}
```

**Interpretation**:
- Borderline case (50% probability)
- Risk and protective factors roughly balanced
- Action: Additional clinical evaluation recommended

---

## 🏥 Clinical Integration Examples

### Example 1: Patient Notification

```python
explanation = explain_single_prediction(model, patient_data, patient_id='P123')

message = f"""
Your PCOS Risk Assessment: {explanation['predicted_probability']:.0%}

Key Findings:
- Your hormone levels (specifically {explanation['top_risk_factors'][0]['feature']})
  show some patterns consistent with PCOS.
  
Recommended Next Steps:
1. Consult with an endocrinologist
2. Confirm with ultrasound
3. Additional hormone tests

This assessment is for screening only and not a diagnosis.
"""
```

### Example 2: Clinical Decision Support

```python
def clinical_recommendation(explanation):
    prob = explanation['predicted_probability']
    
    if prob > 0.7:
        return "URGENT: High PCOS risk. Refer to specialist."
    elif prob > 0.5:
        return "MODERATE: Further evaluation recommended."
    else:
        return "LOW: Monitor patient. No urgent action needed."

recommendation = clinical_recommendation(explanation)
print(recommendation)
```

### Example 3: Research Dashboard

```python
import json

explanations = []
for patient_id, patient_data in patients.items():
    exp = explain_single_prediction(model, patient_data, patient_id)
    explanations.append(exp)

# Save for research analysis
with open('patient_explanations.json', 'w') as f:
    json.dump(explanations, f, indent=2)

# Analyze patterns
average_risk = np.mean([e['predicted_probability'] for e in explanations])
print(f"Average risk in cohort: {average_risk:.1%}")
```

---

## ⚙️ Technical Details

### SHAP vs Tree-Based Importance

| Aspect | SHAP | Tree-Based |
|--------|------|-----------|
| **Theory** | Game theory (Shapley values) | Information gain (Gini) |
| **Speed** | Slower (O(n²)) | Fast (O(n)) |
| **Accuracy** | More accurate for interactions | Good for tree structure |
| **Patient-level** | Yes (local explanations) | No |
| **Computationally Intensive** | Large datasets | Very efficient |

**Our Implementation**: Uses SHAP when available (more accurate), falls back to tree-based when SHAP is too slow.

### How TreeExplainer Works

1. Build a tree structure from the Random Forest
2. For each feature, calculate its contribution using Shapley values
3. For each patient, compute: base_value + sum(feature_contributions) = prediction
4. Sort features by absolute contribution magnitude

---

## 🐛 Troubleshooting

### Issue: "SHAP not installed"

```bash
pip install shap
python run_explain.py
```

### Issue: "Model not found"

Ensure you've run the pipeline first:
```bash
python run_pipeline.py
python run_explain.py
```

### Issue: Slow execution for large datasets

SHAP can be slow for large sample sets. Solutions:

```python
# Use tree-based method instead
importance = get_global_feature_importance(model, method='tree')

# Or use sample of data
sample = X_train.sample(100, random_state=42)
explainer = shap.TreeExplainer(rf_model)
shap_values = explainer.shap_values(sample)
```

### Issue: Features not matching between training and explanation

Ensure feature names are consistent:
```python
# Correct: Provide DataFrame with exact training column names
patient_data.columns = feature_names

# Incorrect: Different column names
patient_data.columns = ['feature_1', 'feature_2', ...]
```

---

## 📚 Further Reading

### Academic Papers
- Lundberg, S. M., & Lee, S. I. (2017). A Unified Approach to Interpreting Model Predictions. *Advances in Neural Information Processing Systems*, 30.
- Shapley, L. S. (1953). A value for n-person games. *Contributions to the Theory of Games*, 2(28), 307-317.

### Clinical ML & Explainability
- Caruana, R., et al. (2015). "Intelligible Models for HealthCare" - *KDD*, 1721-1730
- Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). "Why Should I Trust You?" - *KDD*, 1135-1144

### SHAP Documentation
- Main: https://shap.readthedocs.io/
- Examples: https://github.com/slundberg/shap/tree/master/notebooks
- Tree Explainer: https://shap.readthedocs.io/en/latest/example_notebooks/onboarding/README.html

---

## ✅ Checklist for Clinical Deployment

- [ ] Model trained and saved (`models/pmos_risk_model.pkl`)
- [ ] Explainability module tested (`python run_explain.py`)
- [ ] Sample explanations reviewed (`reports/sample_patient_explanation.json`)
- [ ] Feature names documented and matching
- [ ] Clinicians understand SHAP contributions
- [ ] Disclaimer displayed to users
- [ ] Explanation method logged (SHAP vs tree-based)
- [ ] Performance metrics reviewed

---

## 📞 Support

For questions about SHAP explanations:
1. Review this guide and code comments
2. Check SHAP documentation: https://shap.readthedocs.io/
3. Review `src/explain_model.py` source code
4. Consult with ML/clinical team

---

**Last Updated**: May 14, 2026  
**Version**: 1.0  
**Status**: Ready for Clinical Review

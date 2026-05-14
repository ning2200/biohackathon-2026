"""
PMOS Lens - PCOS Risk Assessment Training Pipeline

This module trains the screening models and saves the artifacts that are needed
later for explainability:
1. The best overall screening model
2. The final Random Forest model used for explainability
3. A reusable preprocessor that can clean and impute new patient rows

The comments are intentionally beginner-friendly so the data flow is easy to
follow end to end.
"""

import json
import pickle
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")


# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "(Main_Dataset)_PCOS_data_without_infertility.xlsx"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"
MODELS_PATH = PROJECT_ROOT / "models"
REPORTS_PATH = PROJECT_ROOT / "reports"

PROCESSED_DATA_PATH.mkdir(parents=True, exist_ok=True)
MODELS_PATH.mkdir(parents=True, exist_ok=True)
REPORTS_PATH.mkdir(parents=True, exist_ok=True)

TARGET_COLUMN = "PCOS (Y/N)"
TEST_SIZE = 0.2
RANDOM_STATE = 42

# These columns are metadata or known confounders, so we do not feed them into
# the model.
COLUMNS_TO_DROP = [
    "Unnamed: 0",
    "Sl. No",
    "Patient File No.",
    "Blood Group",
    "Marraige Status (Yrs)",
    "Pregnant(Y/N)",
    "No. of abortions",
    "I beta-HCG(mIU/mL)",
    "II beta-HCG(mIU/mL)",
]


# ============================================================================
# REUSABLE PREPROCESSOR
# ============================================================================

@dataclass
class PMOSPreprocessor:
    """
    Small helper object that remembers how training data was cleaned.

    Why save this object?
    The model only understands numeric, imputed features in a fixed order.
    New patient rows do not start in that format, so we save the exact cleaning
    and imputation rules that were learned during training.
    """

    target_column_raw: str = TARGET_COLUMN
    columns_to_drop_raw: List[str] = field(default_factory=lambda: list(COLUMNS_TO_DROP))
    imputer: SimpleImputer = field(default_factory=lambda: SimpleImputer(strategy="median"))
    feature_names_: List[str] = field(default_factory=list)
    cleaned_target_column_: str = ""
    reference_values_: Dict[str, float] = field(default_factory=dict)

    @staticmethod
    def clean_column_name(column_name: str) -> str:
        """
        Convert a raw spreadsheet column name into a Python-friendly feature name.

        Example:
        " Age (yrs)" -> "Age_yrs"
        """
        cleaned = re.sub(r"[^0-9a-zA-Z]+", "_", str(column_name).strip())
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
        return cleaned

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return a copy with consistent column names.

        We keep this as a separate step so the same logic can be reused in both
        training and explainability.
        """
        cleaned_df = df.copy()
        cleaned_df.columns = [self.clean_column_name(column) for column in cleaned_df.columns]
        return cleaned_df

    def _cleaned_drop_columns(self) -> List[str]:
        return [self.clean_column_name(column) for column in self.columns_to_drop_raw]

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Turn a raw spreadsheet row into the raw feature table used by the model.

        This step:
        1. Cleans column names
        2. Drops the target column if it is present
        3. Drops non-predictive columns
        4. Converts every feature to numeric where possible
        """
        cleaned_df = self.clean_dataframe(df)

        if not self.cleaned_target_column_:
            self.cleaned_target_column_ = self.clean_column_name(self.target_column_raw)

        feature_df = cleaned_df.drop(columns=[self.cleaned_target_column_], errors="ignore")
        feature_df = feature_df.drop(columns=self._cleaned_drop_columns(), errors="ignore")

        # The spreadsheet stores a few numeric columns as text, so we coerce
        # everything into numbers. Non-numeric leftovers become NaN and are
        # handled by the imputer later.
        for column in feature_df.columns:
            feature_df[column] = pd.to_numeric(feature_df[column], errors="coerce")

        return feature_df

    def split_features_and_target(self, raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Separate the target label from the raw features.
        """
        cleaned_df = self.clean_dataframe(raw_df)
        if not self.cleaned_target_column_:
            self.cleaned_target_column_ = self.clean_column_name(self.target_column_raw)

        if self.cleaned_target_column_ not in cleaned_df.columns:
            raise KeyError(f"Target column '{self.cleaned_target_column_}' not found after cleaning.")

        y = pd.to_numeric(cleaned_df[self.cleaned_target_column_], errors="coerce").astype(int)
        X = self.prepare_features(raw_df)
        return X, y

    def fit(self, raw_feature_df: pd.DataFrame) -> "PMOSPreprocessor":
        """
        Learn the feature order and median values from the training split only.

        Fitting on training data avoids leaking information from the test set.
        """
        prepared_features = self.prepare_features(raw_feature_df)
        self.feature_names_ = list(prepared_features.columns)
        self.imputer.fit(prepared_features[self.feature_names_])

        transformed = pd.DataFrame(
            self.imputer.transform(prepared_features[self.feature_names_]),
            columns=self.feature_names_,
            index=prepared_features.index,
        )

        # These medians are later useful for simple patient-level fallback
        # explanations when SHAP is unavailable.
        self.reference_values_ = transformed.median().to_dict()
        return self

    def transform(self, raw_feature_df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply the saved preprocessing steps to any new feature table.
        """
        if not self.feature_names_:
            raise ValueError("The preprocessor has not been fitted yet.")

        prepared_features = self.prepare_features(raw_feature_df)

        # If a future row is missing a feature column, we add it as NaN so the
        # imputer can fill it using the training median.
        for feature_name in self.feature_names_:
            if feature_name not in prepared_features.columns:
                prepared_features[feature_name] = np.nan

        prepared_features = prepared_features[self.feature_names_]

        transformed = pd.DataFrame(
            self.imputer.transform(prepared_features),
            columns=self.feature_names_,
            index=prepared_features.index,
        )
        return transformed


# ============================================================================
# DATA LOADING
# ============================================================================

def load_dataset() -> pd.DataFrame:
    """
    Load the Excel dataset.

    The project primarily uses the `Full_new` sheet. If that sheet does not
    exist, we fall back to the first sheet in the workbook.
    """
    print("=" * 70)
    print("STEP 1: LOADING DATASET")
    print("=" * 70)

    try:
        df = pd.read_excel(RAW_DATA_PATH, sheet_name="Full_new")
        print(f"Loaded 'Full_new' sheet from {RAW_DATA_PATH.name}")
    except (ValueError, KeyError):
        df = pd.read_excel(RAW_DATA_PATH)
        print(f"Loaded first sheet from {RAW_DATA_PATH.name}")

    print(f"Dataset shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Target distribution for '{TARGET_COLUMN}':")
    print(df[TARGET_COLUMN].value_counts())
    print()

    return df


# ============================================================================
# DATA PREPARATION
# ============================================================================

def prepare_data_for_modeling(
    df: pd.DataFrame, preprocessor: PMOSPreprocessor
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Build the train/test split and fit the reusable preprocessor.
    """
    print("=" * 70)
    print("STEP 2: PREPARING FEATURES")
    print("=" * 70)

    X_raw, y = preprocessor.split_features_and_target(df)

    print(f"Feature matrix before imputation: {X_raw.shape}")
    print(f"Total missing values before imputation: {int(X_raw.isna().sum().sum())}")
    print(f"Number of candidate features: {X_raw.shape[1]}")
    print()

    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_raw,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    preprocessor.fit(X_train_raw)
    X_train = preprocessor.transform(X_train_raw)
    X_test = preprocessor.transform(X_test_raw)

    print(f"Training set: {X_train.shape[0]} rows")
    print(f"Test set: {X_test.shape[0]} rows")
    print(f"Missing values after imputation: {int(X_train.isna().sum().sum() + X_test.isna().sum().sum())}")
    print("Sample cleaned feature names:")
    for feature_name in preprocessor.feature_names_[:5]:
        print(f"  - {feature_name}")
    print()

    # Saving a processed sample is helpful when debugging later.
    X_train.head(25).to_csv(PROCESSED_DATA_PATH / "training_feature_sample.csv", index=False)

    return X_train, X_test, y_train, y_test


# ============================================================================
# MODEL TRAINING
# ============================================================================

def train_logistic_regression(X_train: pd.DataFrame, y_train: pd.Series) -> Pipeline:
    """
    Baseline model with scaling.
    """
    print("=" * 70)
    print("STEP 3A: TRAINING LOGISTIC REGRESSION")
    print("=" * 70)

    lr_model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("logistic", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
        ]
    )
    lr_model.fit(X_train, y_train)

    print("Logistic Regression trained successfully")
    print()
    return lr_model


def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
    """
    Final tree-based model used for explainability.
    """
    print("=" * 70)
    print("STEP 3B: TRAINING RANDOM FOREST")
    print("=" * 70)

    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    rf_model.fit(X_train, y_train)

    print("Random Forest trained successfully")
    print()
    return rf_model


# ============================================================================
# MODEL EVALUATION
# ============================================================================

def calculate_metrics(y_true: pd.Series, y_pred: np.ndarray, y_pred_proba: np.ndarray) -> Dict[str, float]:
    """
    Calculate the main classification metrics used in the project.
    """
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred),
        "recall": recall_score(y_true, y_pred),
        "specificity": tn / (tn + fp),
        "f1_score": f1_score(y_true, y_pred),
        "roc_auc": roc_auc_score(y_true, y_pred_proba),
        "confusion_matrix": cm.tolist(),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
    }


def evaluate_models(
    lr_model: Pipeline,
    rf_model: RandomForestClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Tuple[object, Dict[str, float], str, Dict[str, float], Dict[str, float]]:
    """
    Compare both models and keep the one with the better recall for screening.
    """
    print("=" * 70)
    print("STEP 4: EVALUATING MODELS")
    print("=" * 70)

    lr_pred = lr_model.predict(X_test)
    lr_pred_proba = lr_model.predict_proba(X_test)[:, 1]
    lr_metrics = calculate_metrics(y_test, lr_pred, lr_pred_proba)

    rf_pred = rf_model.predict(X_test)
    rf_pred_proba = rf_model.predict_proba(X_test)[:, 1]
    rf_metrics = calculate_metrics(y_test, rf_pred, rf_pred_proba)

    print("--- Logistic Regression ---")
    print(f"Accuracy:    {lr_metrics['accuracy']:.4f}")
    print(f"Precision:   {lr_metrics['precision']:.4f}")
    print(f"Recall:      {lr_metrics['recall']:.4f}")
    print(f"Specificity: {lr_metrics['specificity']:.4f}")
    print(f"F1-Score:    {lr_metrics['f1_score']:.4f}")
    print(f"ROC-AUC:     {lr_metrics['roc_auc']:.4f}")
    print()

    print("--- Random Forest ---")
    print(f"Accuracy:    {rf_metrics['accuracy']:.4f}")
    print(f"Precision:   {rf_metrics['precision']:.4f}")
    print(f"Recall:      {rf_metrics['recall']:.4f}")
    print(f"Specificity: {rf_metrics['specificity']:.4f}")
    print(f"F1-Score:    {rf_metrics['f1_score']:.4f}")
    print(f"ROC-AUC:     {rf_metrics['roc_auc']:.4f}")
    print()

    if lr_metrics["recall"] >= rf_metrics["recall"]:
        best_model = lr_model
        best_metrics = lr_metrics
        best_model_name = "Logistic Regression"
    else:
        best_model = rf_model
        best_metrics = rf_metrics
        best_model_name = "Random Forest"

    print(f"Selected best screening model: {best_model_name}")
    print()

    return best_model, best_metrics, best_model_name, lr_metrics, rf_metrics


# ============================================================================
# THRESHOLD TUNING
# ============================================================================

def tune_decision_threshold(model: object, X_test: pd.DataFrame, y_test: pd.Series) -> float:
    """
    Search for a threshold with strong recall while keeping specificity usable.
    """
    print("=" * 70)
    print("STEP 5: TUNING DECISION THRESHOLD")
    print("=" * 70)

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    thresholds = np.arange(0.2, 0.85, 0.05)
    results = []

    for threshold in thresholds:
        y_pred_custom = (y_pred_proba >= threshold).astype(int)
        cm = confusion_matrix(y_test, y_pred_custom)
        tn, fp, _, _ = cm.ravel()

        results.append(
            {
                "threshold": float(threshold),
                "recall": recall_score(y_test, y_pred_custom),
                "specificity": tn / (tn + fp),
                "f1": f1_score(y_test, y_pred_custom),
            }
        )

    results_df = pd.DataFrame(results)
    valid_results = results_df[results_df["specificity"] >= 0.6]
    if not valid_results.empty:
        best_row = valid_results.loc[valid_results["recall"].idxmax()]
    else:
        best_row = results_df.loc[results_df["recall"].idxmax()]

    print(results_df.to_string(index=False))
    print()
    print(f"Selected threshold: {best_row['threshold']:.2f}")
    print(f"Recall at threshold: {best_row['recall']:.4f}")
    print(f"Specificity at threshold: {best_row['specificity']:.4f}")
    print()

    return float(best_row["threshold"])


# ============================================================================
# ARTIFACT SAVING
# ============================================================================

def save_models_and_results(
    best_model: object,
    best_model_name: str,
    rf_model: RandomForestClassifier,
    preprocessor: PMOSPreprocessor,
    best_metrics: Dict[str, float],
    threshold: float,
    lr_metrics: Dict[str, float],
    rf_metrics: Dict[str, float],
) -> Tuple[Path, Path, Path]:
    """
    Save the model artifacts used by both prediction and explainability.
    """
    print("=" * 70)
    print("STEP 6: SAVING ARTIFACTS")
    print("=" * 70)

    best_model_path = MODELS_PATH / "pmos_risk_model.pkl"
    rf_model_path = MODELS_PATH / "pmos_random_forest_model.pkl"
    preprocessor_path = MODELS_PATH / "pmos_preprocessor.pkl"

    with open(best_model_path, "wb") as file_handle:
        pickle.dump(best_model, file_handle)

    with open(rf_model_path, "wb") as file_handle:
        pickle.dump(rf_model, file_handle)

    with open(preprocessor_path, "wb") as file_handle:
        pickle.dump(preprocessor, file_handle)

    print(f"Saved best screening model to {best_model_path}")
    print(f"Saved Random Forest model to {rf_model_path}")
    print(f"Saved reusable preprocessor to {preprocessor_path}")

    metrics_payload = {
        "best_model_type": best_model_name,
        "best_model_path": str(best_model_path),
        "random_forest_model_path": str(rf_model_path),
        "preprocessor_path": str(preprocessor_path),
        "decision_threshold": threshold,
        "test_size": TEST_SIZE,
        "random_state": RANDOM_STATE,
        "feature_count": len(preprocessor.feature_names_),
        "feature_names": preprocessor.feature_names_,
        "metrics_threshold_0_5": best_metrics,
        "metrics_lr": lr_metrics,
        "metrics_rf": rf_metrics,
    }

    metrics_path = REPORTS_PATH / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as file_handle:
        json.dump(metrics_payload, file_handle, indent=2)
    print(f"Saved metrics to {metrics_path}")

    # We always plot the Random Forest importances because that is the model
    # used in the explainability module.
    importances = rf_model.feature_importances_
    ranking = np.argsort(importances)[::-1][:20]

    plt.figure(figsize=(12, 6))
    plt.title("Top 20 Random Forest Feature Importances", fontsize=14, fontweight="bold")
    plt.bar(range(len(ranking)), importances[ranking])
    plt.xticks(
        range(len(ranking)),
        np.array(preprocessor.feature_names_)[ranking],
        rotation=45,
        ha="right",
    )
    plt.ylabel("Importance Score")
    plt.tight_layout()

    plot_path = REPORTS_PATH / "feature_importance.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved Random Forest importance plot to {plot_path}")
    print()

    return best_model_path, rf_model_path, preprocessor_path


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main() -> None:
    """
    Execute the full training pipeline.
    """
    print()
    print("=" * 70)
    print("PMOS LENS - PCOS RISK ASSESSMENT MODEL PIPELINE")
    print("=" * 70)
    print()

    df = load_dataset()
    preprocessor = PMOSPreprocessor()
    X_train, X_test, y_train, y_test = prepare_data_for_modeling(df, preprocessor)

    lr_model = train_logistic_regression(X_train, y_train)
    rf_model = train_random_forest(X_train, y_train)

    best_model, best_metrics, best_model_name, lr_metrics, rf_metrics = evaluate_models(
        lr_model,
        rf_model,
        X_test,
        y_test,
    )

    best_threshold = tune_decision_threshold(best_model, X_test, y_test)

    best_model_path, rf_model_path, preprocessor_path = save_models_and_results(
        best_model=best_model,
        best_model_name=best_model_name,
        rf_model=rf_model,
        preprocessor=preprocessor,
        best_metrics=best_metrics,
        threshold=best_threshold,
        lr_metrics=lr_metrics,
        rf_metrics=rf_metrics,
    )

    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"Best screening model: {best_model_name}")
    print(f"Best threshold: {best_threshold:.2f}")
    print(f"Best model recall: {best_metrics['recall']:.4f}")
    print(f"Random Forest model path: {rf_model_path}")
    print(f"Preprocessor path: {preprocessor_path}")
    print(f"Primary prediction model path: {best_model_path}")
    print()
    print("This model is for clinical triage support only.")
    print()


if __name__ == "__main__":
    main()

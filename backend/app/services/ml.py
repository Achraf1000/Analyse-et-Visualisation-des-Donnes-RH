from __future__ import annotations

import joblib
import pandas as pd
from fastapi import HTTPException, status
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy.orm import Session

from app.core.config import MODEL_DIR
from app.models.entities import EmployeeRecord, ModelRun
from app.services.analytics import get_active_import


NUMERIC_FEATURES = ["age", "salary", "tenure_years", "training_hours", "performance_score", "satisfaction_score"]
CATEGORICAL_FEATURES = ["department", "gender"]


def _risk_level(probability: float) -> str:
    if probability < 0.33:
        return "low"
    if probability <= 0.66:
        return "medium"
    return "high"


def train_attrition_model(db: Session) -> dict:
    import_run = get_active_import(db)
    records = db.query(EmployeeRecord).filter(
        EmployeeRecord.import_id == import_run.id,
        EmployeeRecord.is_valid.is_(True),
    ).all()
    if len(records) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le dataset actif est trop petit pour entraîner un modèle fiable.",
        )

    dataframe = pd.DataFrame(
        [
            {
                "record_id": record.id,
                "age": record.age,
                "salary": record.salary,
                "tenure_years": record.tenure_years,
                "training_hours": record.training_hours,
                "performance_score": record.performance_score,
                "satisfaction_score": record.satisfaction_score,
                "department": record.department,
                "gender": record.gender,
                "attrition": record.attrition,
            }
            for record in records
        ]
    )
    if dataframe["attrition"].nunique() < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le dataset actif doit contenir au moins deux classes de départ pour entraîner le modèle.",
        )

    features = dataframe[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    target = dataframe["attrition"]
    test_size = 0.25 if len(dataframe) >= 12 else 0.4
    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=test_size,
        random_state=42,
        stratify=target,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", Pipeline([("scaler", StandardScaler())]), NUMERIC_FEATURES),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=500)),
        ]
    )
    model.fit(X_train, y_train)

    test_probabilities = model.predict_proba(X_test)[:, 1]
    test_predictions = (test_probabilities >= 0.5).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(y_test, test_predictions)),
        "precision": float(precision_score(y_test, test_predictions, zero_division=0)),
        "recall": float(recall_score(y_test, test_predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, test_probabilities)),
    }
    confusion = confusion_matrix(y_test, test_predictions).tolist()

    trained_preprocessor = model.named_steps["preprocessor"]
    classifier = model.named_steps["classifier"]
    feature_names = trained_preprocessor.get_feature_names_out()
    coefficients = [
        {"feature": feature.replace("numeric__", "").replace("categorical__", ""), "coefficient": round(float(coef), 4)}
        for feature, coef in zip(feature_names, classifier.coef_[0], strict=False)
    ]
    coefficients.sort(key=lambda item: abs(item["coefficient"]), reverse=True)

    artifact_path = MODEL_DIR / f"attrition_model_import_{import_run.id}.joblib"
    joblib.dump(model, artifact_path)

    full_probabilities = model.predict_proba(features)[:, 1]
    probability_by_record = dict(zip(dataframe["record_id"], full_probabilities, strict=False))
    for record in records:
        probability = float(probability_by_record.get(record.id, 0.0))
        record.risk_probability = probability
        record.risk_level = _risk_level(probability)

    model_run = ModelRun(
        import_id=import_run.id,
        status="trained",
        artifact_path=str(artifact_path),
        metrics=metrics,
        coefficients=coefficients[:12],
        confusion_matrix=confusion,
        summary={"records": len(records), "features": list(feature_names)},
    )
    db.add(model_run)
    db.commit()
    db.refresh(model_run)

    return {
        "modelRunId": model_run.id,
        "trainedAt": model_run.trained_at,
        "metrics": {
            "accuracy": round(metrics["accuracy"], 4),
            "precision": round(metrics["precision"], 4),
            "recall": round(metrics["recall"], 4),
            "rocAuc": round(metrics["roc_auc"], 4),
        },
        "confusionMatrix": confusion,
        "coefficients": coefficients[:12],
    }

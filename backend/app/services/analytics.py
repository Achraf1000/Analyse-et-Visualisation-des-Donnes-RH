from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.entities import EmployeeRecord, ImportRun, ModelRun
from app.schemas.api import KPIResponse


def get_active_import(db: Session) -> ImportRun:
    import_run = db.query(ImportRun).filter(ImportRun.is_active.is_(True)).first()
    if not import_run:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Aucun import actif. Activez un dataset valide pour poursuivre.",
        )
    return import_run


def get_filtered_records(
    db: Session,
    *,
    department: str | None = None,
    gender: str | None = None,
    tenure_min: float | None = None,
    tenure_max: float | None = None,
    age_min: float | None = None,
    age_max: float | None = None,
) -> tuple[ImportRun, list[EmployeeRecord]]:
    import_run = get_active_import(db)
    query = db.query(EmployeeRecord).filter(
        EmployeeRecord.import_id == import_run.id,
        EmployeeRecord.is_valid.is_(True),
    )
    if department:
        query = query.filter(EmployeeRecord.department == department)
    if gender:
        query = query.filter(EmployeeRecord.gender == gender)
    if tenure_min is not None:
        query = query.filter(EmployeeRecord.tenure_years >= tenure_min)
    if tenure_max is not None:
        query = query.filter(EmployeeRecord.tenure_years <= tenure_max)
    if age_min is not None:
        query = query.filter(EmployeeRecord.age >= age_min)
    if age_max is not None:
        query = query.filter(EmployeeRecord.age <= age_max)
    return import_run, query.all()


def _records_to_dataframe(records: list[EmployeeRecord]) -> pd.DataFrame:
    rows = [
        {
            "record_id": record.id,
            "employee_id": record.employee_id,
            "full_name": record.full_name,
            "department": record.department,
            "gender": record.gender,
            "age": record.age,
            "salary": record.salary,
            "tenure_years": record.tenure_years,
            "training_hours": record.training_hours,
            "performance_score": record.performance_score,
            "satisfaction_score": record.satisfaction_score,
            "attrition": record.attrition,
            "risk_probability": record.risk_probability,
            "risk_level": record.risk_level,
        }
        for record in records
    ]
    return pd.DataFrame(rows)


def _empty_kpi_payload() -> dict[str, float | int]:
    return {
        "headcount": 0,
        "turnoverRate": 0.0,
        "averageTenure": 0.0,
        "averageSalary": 0.0,
        "totalCost": 0.0,
    }


def get_kpi_payload(db: Session, **filters: Any) -> dict[str, float | int]:
    _, records = get_filtered_records(db, **filters)
    if not records:
        return _empty_kpi_payload()
    dataframe = _records_to_dataframe(records)
    return {
        "headcount": int(len(dataframe)),
        "turnoverRate": round(float(dataframe["attrition"].mean() * 100), 2),
        "averageTenure": round(float(dataframe["tenure_years"].mean()), 2),
        "averageSalary": round(float(dataframe["salary"].mean()), 2),
        "totalCost": round(float(dataframe["salary"].sum()), 2),
    }


def _department_chart(dataframe: pd.DataFrame) -> list[dict[str, float | str]]:
    if dataframe.empty:
        return []
    grouped = dataframe.groupby("department").agg(count=("employee_id", "count"), turnover=("attrition", "mean")).reset_index()
    return [
        {
            "name": row["department"],
            "value": int(row["count"]),
            "secondaryValue": round(float(row["turnover"] * 100), 2),
        }
        for _, row in grouped.iterrows()
    ]


def _gender_chart(dataframe: pd.DataFrame) -> list[dict[str, float | str]]:
    if dataframe.empty:
        return []
    grouped = dataframe.groupby("gender").size().reset_index(name="count")
    return [{"name": row["gender"], "value": int(row["count"])} for _, row in grouped.iterrows()]


def _tenure_buckets(dataframe: pd.DataFrame) -> list[dict[str, float | str]]:
    if dataframe.empty:
        return []
    bins = [0, 1, 3, 5, 10, float("inf")]
    labels = ["0-1 an", "1-3 ans", "3-5 ans", "5-10 ans", "10+ ans"]
    with_buckets = dataframe.copy()
    with_buckets["bucket"] = pd.cut(
        with_buckets["tenure_years"],
        bins=bins,
        labels=labels,
        right=False,
        include_lowest=True,
    )
    grouped = with_buckets.groupby("bucket").size().reset_index(name="count")
    return [{"name": str(row["bucket"]), "value": int(row["count"])} for _, row in grouped.iterrows()]


def _risk_distribution(dataframe: pd.DataFrame) -> list[dict[str, float | str]]:
    if dataframe.empty or "risk_level" not in dataframe:
        return []
    series = dataframe["risk_level"].fillna("Non évalué").value_counts()
    return [{"name": str(index), "value": int(value)} for index, value in series.items()]


def _filter_options(db: Session, import_run: ImportRun) -> dict[str, list[str]]:
    records = db.query(EmployeeRecord).filter(
        EmployeeRecord.import_id == import_run.id,
        EmployeeRecord.is_valid.is_(True),
    ).all()
    departments = sorted({record.department for record in records if record.department})
    genders = sorted({record.gender for record in records if record.gender})
    return {"departments": departments, "genders": genders}


def get_filter_options_payload(db: Session) -> dict[str, list[str]]:
    import_run = get_active_import(db)
    return _filter_options(db, import_run)


def get_dashboard_payload(db: Session, **filters: Any) -> dict[str, Any]:
    import_run, records = get_filtered_records(db, **filters)
    dataframe = _records_to_dataframe(records)
    latest_model = db.query(ModelRun).filter(ModelRun.import_id == import_run.id).order_by(ModelRun.trained_at.desc()).first()
    return {
        "kpis": KPIResponse.model_validate(get_kpi_payload(db, **filters)).model_dump(by_alias=True),
        "filters": _filter_options(db, import_run),
        "charts": {
            "departmentHeadcount": _department_chart(dataframe),
            "genderDistribution": _gender_chart(dataframe),
            "tenureDistribution": _tenure_buckets(dataframe),
            "riskDistribution": _risk_distribution(dataframe),
        },
        "meta": {
            "activeImportId": import_run.id,
            "totalRecords": int(len(dataframe)),
            "lastModelTrainedAt": latest_model.trained_at.isoformat() if latest_model else None,
        },
    }


def get_correlation_payload(db: Session, **filters: Any) -> dict[str, Any]:
    _, records = get_filtered_records(db, **filters)
    dataframe = _records_to_dataframe(records)
    numeric_columns = ["training_hours", "performance_score", "satisfaction_score", "tenure_years", "salary", "attrition", "age"]
    if dataframe.empty:
        return {
            "labels": numeric_columns,
            "matrix": [[0 for _ in numeric_columns] for _ in numeric_columns],
            "scatterSeries": {"trainingVsPerformance": [], "satisfactionVsTenure": [], "salaryVsSatisfaction": []},
            "insights": ["Aucune donnée valide ne correspond aux filtres sélectionnés."],
        }

    correlation_matrix = dataframe[numeric_columns].corr(numeric_only=True).fillna(0)
    scatter_series = {
        "trainingVsPerformance": [
            {
                "employeeId": row["employee_id"],
                "x": float(row["training_hours"]),
                "y": float(row["performance_score"]),
                "attrition": int(row["attrition"]),
                "department": row["department"],
            }
            for _, row in dataframe.iterrows()
        ],
        "satisfactionVsTenure": [
            {
                "employeeId": row["employee_id"],
                "x": float(row["satisfaction_score"]),
                "y": float(row["tenure_years"]),
                "attrition": int(row["attrition"]),
                "department": row["department"],
            }
            for _, row in dataframe.iterrows()
        ],
        "salaryVsSatisfaction": [
            {
                "employeeId": row["employee_id"],
                "x": float(row["salary"]),
                "y": float(row["satisfaction_score"]),
                "attrition": int(row["attrition"]),
                "department": row["department"],
            }
            for _, row in dataframe.iterrows()
        ],
    }

    strongest_pairs = []
    for index, row_name in enumerate(numeric_columns):
        for column_name in numeric_columns[index + 1 :]:
            strongest_pairs.append((row_name, column_name, abs(float(correlation_matrix.loc[row_name, column_name]))))
    strongest_pairs.sort(key=lambda item: item[2], reverse=True)
    insights = [f"Corrélation notable entre {left} et {right}: {score:.2f}." for left, right, score in strongest_pairs[:3]]

    return {
        "labels": numeric_columns,
        "matrix": [[round(float(value), 3) for value in row] for row in correlation_matrix.to_numpy()],
        "scatterSeries": scatter_series,
        "insights": insights,
    }


def latest_model_payload(db: Session, import_run: ImportRun | None = None) -> dict[str, Any] | None:
    if import_run is None:
        import_run = get_active_import(db)
    model_run = db.query(ModelRun).filter(ModelRun.import_id == import_run.id).order_by(ModelRun.trained_at.desc()).first()
    if not model_run:
        return None
    return {
        "modelRunId": model_run.id,
        "trainedAt": model_run.trained_at,
        "metrics": {
            "accuracy": round(float(model_run.metrics.get("accuracy", 0)), 4),
            "precision": round(float(model_run.metrics.get("precision", 0)), 4),
            "recall": round(float(model_run.metrics.get("recall", 0)), 4),
            "rocAuc": round(float(model_run.metrics.get("roc_auc", 0)), 4),
        },
        "confusionMatrix": model_run.confusion_matrix or [[0, 0], [0, 0]],
        "coefficients": model_run.coefficients or [],
    }


def get_predictions_payload(db: Session, **filters: Any) -> dict[str, Any]:
    import_run, records = get_filtered_records(db, **filters)
    items = [
        {
            "recordId": record.id,
            "employeeId": record.employee_id,
            "fullName": record.full_name,
            "department": record.department,
            "gender": record.gender,
            "tenureYears": record.tenure_years,
            "performanceScore": record.performance_score,
            "satisfactionScore": record.satisfaction_score,
            "salary": record.salary,
            "riskProbability": round(float(record.risk_probability), 4) if record.risk_probability is not None else 0.0,
            "riskLevel": record.risk_level or "non_evalue",
        }
        for record in sorted(records, key=lambda item: item.risk_probability or 0, reverse=True)
    ]
    return {"modelRun": latest_model_payload(db, import_run), "items": items}

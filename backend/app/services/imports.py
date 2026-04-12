from __future__ import annotations

import csv
import io
import re
import unicodedata
from collections import Counter
from datetime import date, datetime
from typing import Any

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, func
from sqlalchemy.orm import Session

from app.models.entities import EmployeeRecord, ImportRun, ValidationIssue


CANONICAL_ALIASES = {
    "employee_id": ["employee_id", "employeeid", "id", "matricule", "emp_id", "personnel_id", "employee_number"],
    "full_name": ["full_name", "fullname", "name", "nom", "employee_name"],
    "department": ["department", "departement", "dept", "service", "business_unit"],
    "gender": ["gender", "sexe", "sex", "genre"],
    "age": ["age", "employee_age"],
    "birth_date": ["birth_date", "birthdate", "date_naissance", "dob", "dateofbirth"],
    "salary": ["salary", "salaire", "monthly_salary", "monthly_income", "compensation", "wage"],
    "hire_date": ["hire_date", "date_embauche", "start_date", "employment_date", "datehire"],
    "tenure_years": ["tenure_years", "anciennete", "seniority", "tenure", "years_at_company", "total_working_years"],
    "training_hours": ["training_hours", "formation", "formation_heures", "hours_training", "training", "training_times_last_year"],
    "performance_score": ["performance_score", "performance", "evaluation", "rating", "score_performance", "performance_rating"],
    "satisfaction_score": [
        "satisfaction_score",
        "satisfaction",
        "engagement",
        "score_satisfaction",
        "job_satisfaction",
        "environment_satisfaction",
        "relationship_satisfaction",
        "work_life_balance",
    ],
    "attrition": ["attrition", "turnover", "departure", "left_company", "quit", "depart"],
}

REQUIRED_GROUPS = {
    "employee_id": ["employee_id"],
    "department": ["department"],
    "gender": ["gender"],
    "salary": ["salary"],
    "training_hours": ["training_hours"],
    "performance_score": ["performance_score"],
    "satisfaction_score": ["satisfaction_score"],
    "attrition": ["attrition"],
    "age_or_birth_date": ["age", "birth_date"],
    "hire_date_or_tenure_years": ["hire_date", "tenure_years"],
}

GENDER_MAP = {
    "m": "Homme",
    "male": "Homme",
    "man": "Homme",
    "homme": "Homme",
    "f": "Femme",
    "female": "Femme",
    "woman": "Femme",
    "femme": "Femme",
}

ATTRITION_MAP = {
    "1": 1,
    "true": 1,
    "yes": 1,
    "oui": 1,
    "depart": 1,
    "left": 1,
    "0": 0,
    "false": 0,
    "no": 0,
    "non": 0,
    "stay": 0,
}


def normalize_header(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    cleaned = "".join(char if char.isalnum() else "_" for char in value.lower())
    return "_".join(chunk for chunk in cleaned.split("_") if chunk)


def _is_missing(value: Any) -> bool:
    return value is None or pd.isna(value) or (isinstance(value, str) and not value.strip())


def _clean_string(value: Any) -> str | None:
    if _is_missing(value):
        return None
    text = str(value).strip()
    return text or None


def _clean_float(value: Any) -> float | None:
    if _is_missing(value):
        return None
    text = str(value).strip().replace(" ", "").replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _clean_date(value: Any) -> date | None:
    if _is_missing(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return None
    return parsed.date()


def _normalize_gender(value: Any) -> str | None:
    text = _clean_string(value)
    if not text:
        return None
    return GENDER_MAP.get(text.lower(), text.title())


def _normalize_attrition(value: Any) -> int | None:
    if _is_missing(value):
        return None
    text = str(value).strip().lower()
    if text in ATTRITION_MAP:
        return ATTRITION_MAP[text]
    try:
        number = int(float(text))
    except ValueError:
        return None
    return number if number in (0, 1) else None


def _calculate_age_from_birth_date(birth_date: date) -> float:
    today = date.today()
    years = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return float(years)


def _calculate_tenure_from_hire_date(hire_date: date) -> float:
    return round((date.today() - hire_date).days / 365.25, 2)


def detect_mapping(columns: list[str]) -> tuple[dict[str, str | None], list[str]]:
    normalized_columns: dict[str, str] = {}
    for column in columns:
        normalized_columns.setdefault(normalize_header(column), column)

    mapping: dict[str, str | None] = {key: None for key in CANONICAL_ALIASES}
    for canonical, aliases in CANONICAL_ALIASES.items():
        for alias in aliases:
            normalized_alias = normalize_header(alias)
            if normalized_alias in normalized_columns:
                mapping[canonical] = normalized_columns[normalized_alias]
                break

    missing_required_fields = []
    for group_name, options in REQUIRED_GROUPS.items():
        if not any(mapping.get(option) for option in options):
            missing_required_fields.append(group_name)

    return mapping, missing_required_fields


def _build_raw_payload(row: pd.Series, mapping: dict[str, str | None]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for canonical, source_column in mapping.items():
        if source_column:
            value = row.get(source_column)
            payload[canonical] = None if pd.isna(value) else value
    return payload


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    birth_date = _clean_date(payload.get("birth_date"))
    hire_date = _clean_date(payload.get("hire_date"))
    age = _clean_float(payload.get("age"))
    tenure_years = _clean_float(payload.get("tenure_years"))
    if birth_date:
        age = _calculate_age_from_birth_date(birth_date)
    if hire_date:
        tenure_years = _calculate_tenure_from_hire_date(hire_date)

    return {
        "employee_id": _clean_string(payload.get("employee_id")),
        "full_name": _clean_string(payload.get("full_name")),
        "department": _clean_string(payload.get("department")),
        "gender": _normalize_gender(payload.get("gender")),
        "age": age,
        "birth_date": birth_date,
        "salary": _clean_float(payload.get("salary")),
        "hire_date": hire_date,
        "tenure_years": tenure_years,
        "training_hours": _clean_float(payload.get("training_hours")),
        "performance_score": _clean_float(payload.get("performance_score")),
        "satisfaction_score": _clean_float(payload.get("satisfaction_score")),
        "attrition": _normalize_attrition(payload.get("attrition")),
    }


def _issue(field_name: str | None, code: str, message: str) -> dict[str, str | None]:
    return {"field_name": field_name, "issue_code": code, "message": message, "severity": "error"}


def validate_payload(normalized: dict[str, Any], duplicate_counter: Counter[str]) -> list[dict[str, str | None]]:
    issues: list[dict[str, str | None]] = []
    employee_id = normalized.get("employee_id")
    if not employee_id:
        issues.append(_issue("employee_id", "missing_employee_id", "Identifiant employé manquant."))
    elif duplicate_counter.get(employee_id.lower(), 0) > 1:
        issues.append(_issue("employee_id", "duplicate_employee_id", "Identifiant employé dupliqué dans le fichier."))

    if not normalized.get("department"):
        issues.append(_issue("department", "missing_department", "Département manquant."))
    if not normalized.get("gender"):
        issues.append(_issue("gender", "missing_gender", "Sexe manquant."))

    age = normalized.get("age")
    if age is None:
        issues.append(_issue("age", "missing_age", "Âge ou date de naissance manquant."))
    elif not 16 <= age <= 75:
        issues.append(_issue("age", "invalid_age", "Âge hors de la plage autorisée [16, 75]."))

    salary = normalized.get("salary")
    if salary is None:
        issues.append(_issue("salary", "missing_salary", "Salaire manquant."))
    elif salary <= 0:
        issues.append(_issue("salary", "invalid_salary", "Salaire inférieur ou égal à zéro."))

    hire_date = normalized.get("hire_date")
    if hire_date and hire_date > date.today():
        issues.append(_issue("hire_date", "future_hire_date", "La date d'embauche ne peut pas être future."))

    tenure_years = normalized.get("tenure_years")
    if tenure_years is None:
        issues.append(_issue("tenure_years", "missing_tenure", "Ancienneté ou date d'embauche manquante."))
    elif tenure_years < 0:
        issues.append(_issue("tenure_years", "negative_tenure", "Ancienneté négative."))

    training_hours = normalized.get("training_hours")
    if training_hours is None:
        issues.append(_issue("training_hours", "missing_training_hours", "Heures de formation manquantes."))
    elif training_hours < 0:
        issues.append(_issue("training_hours", "invalid_training_hours", "Heures de formation négatives."))

    performance_score = normalized.get("performance_score")
    if performance_score is None:
        issues.append(_issue("performance_score", "missing_performance", "Score de performance manquant."))
    elif not 1 <= performance_score <= 5:
        issues.append(_issue("performance_score", "invalid_performance", "Le score de performance doit être compris entre 1 et 5."))

    satisfaction_score = normalized.get("satisfaction_score")
    if satisfaction_score is None:
        issues.append(_issue("satisfaction_score", "missing_satisfaction", "Score de satisfaction manquant."))
    elif not 1 <= satisfaction_score <= 5:
        issues.append(_issue("satisfaction_score", "invalid_satisfaction", "Le score de satisfaction doit être compris entre 1 et 5."))

    attrition = normalized.get("attrition")
    if attrition is None:
        issues.append(_issue("attrition", "invalid_attrition", "La variable de départ doit être binaire (0/1, oui/non)."))

    return issues


def _compute_summary(db: Session, import_run: ImportRun) -> dict[str, int]:
    db.flush()
    total_rows = db.query(func.count(EmployeeRecord.id)).filter(EmployeeRecord.import_id == import_run.id).scalar() or 0
    valid_rows = db.query(func.count(EmployeeRecord.id)).filter(
        EmployeeRecord.import_id == import_run.id,
        EmployeeRecord.is_valid.is_(True),
    ).scalar() or 0
    invalid_rows = total_rows - valid_rows
    blocking_issues = db.query(func.count(ValidationIssue.id)).filter(ValidationIssue.import_id == import_run.id).scalar() or 0
    summary = {
        "total_rows": int(total_rows),
        "valid_rows": int(valid_rows),
        "invalid_rows": int(invalid_rows),
        "blocking_issues": int(blocking_issues),
        "warning_issues": 0,
    }
    import_run.total_rows = summary["total_rows"]
    import_run.valid_rows = summary["valid_rows"]
    import_run.invalid_rows = summary["invalid_rows"]
    import_run.validation_summary = summary
    if import_run.missing_required_fields:
        import_run.status = "missing_required_fields"
    elif invalid_rows:
        import_run.status = "validated_with_errors"
    else:
        import_run.status = "validated"
    return summary


def _sync_record(record: EmployeeRecord, normalized: dict[str, Any], raw_payload: dict[str, Any] | None = None) -> None:
    record.employee_id = normalized.get("employee_id")
    record.full_name = normalized.get("full_name")
    record.department = normalized.get("department")
    record.gender = normalized.get("gender")
    record.age = normalized.get("age")
    record.birth_date = normalized.get("birth_date")
    record.salary = normalized.get("salary")
    record.hire_date = normalized.get("hire_date")
    record.tenure_years = normalized.get("tenure_years")
    record.training_hours = normalized.get("training_hours")
    record.performance_score = normalized.get("performance_score")
    record.satisfaction_score = normalized.get("satisfaction_score")
    record.attrition = normalized.get("attrition")
    record.raw_payload = raw_payload if raw_payload is not None else record.raw_payload
    record.normalized_payload = {
        key: value.isoformat() if isinstance(value, date) else value for key, value in normalized.items()
    }
    record.risk_probability = None
    record.risk_level = None


def revalidate_import(db: Session, import_run: ImportRun) -> dict[str, int]:
    records = db.query(EmployeeRecord).filter(EmployeeRecord.import_id == import_run.id).order_by(EmployeeRecord.row_index).all()
    duplicate_counter = Counter(record.employee_id.lower() for record in records if record.employee_id)

    db.execute(delete(ValidationIssue).where(ValidationIssue.import_id == import_run.id))
    for record in records:
        normalized = normalize_payload(record.raw_payload or record.normalized_payload or {})
        _sync_record(record, normalized)
        issues = validate_payload(normalized, duplicate_counter)
        record.is_valid = not issues
        for issue in issues:
            db.add(
                ValidationIssue(
                    import_id=import_run.id,
                    record_id=record.id,
                    row_index=record.row_index,
                    field_name=issue["field_name"],
                    issue_code=issue["issue_code"],
                    message=issue["message"],
                    severity=issue["severity"],
                )
            )

    db.flush()
    summary = _compute_summary(db, import_run)
    db.commit()
    db.refresh(import_run)
    return summary


def _parse_dataframe_from_upload(contents: bytes) -> pd.DataFrame:
    sample = contents[:4096].decode("utf-8-sig", errors="ignore")
    delimiter = ","
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","

    buffer = io.BytesIO(contents)
    try:
        return pd.read_csv(buffer, sep=delimiter)
    except UnicodeDecodeError:
        buffer.seek(0)
        return pd.read_csv(buffer, sep=delimiter, encoding="latin-1")


def serialize_import(import_run: ImportRun) -> dict[str, Any]:
    return {
        "importId": import_run.id,
        "filename": import_run.filename,
        "status": import_run.status,
        "isActive": import_run.is_active,
        "uploadedAt": import_run.uploaded_at,
        "detectedMapping": import_run.detected_mapping or {},
        "missingRequiredFields": import_run.missing_required_fields or [],
        "validationSummary": import_run.validation_summary or {},
        "totalRows": import_run.total_rows,
        "validRows": import_run.valid_rows,
        "invalidRows": import_run.invalid_rows,
    }


async def create_import_from_csv(db: Session, upload_file: UploadFile) -> ImportRun:
    contents = await upload_file.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le fichier CSV est vide.")

    try:
        dataframe = _parse_dataframe_from_upload(contents)
    except Exception as error:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de lire le fichier CSV: {error}",
        ) from error

    mapping, missing_required_fields = detect_mapping(dataframe.columns.tolist())
    import_run = ImportRun(
        filename=upload_file.filename or "import.csv",
        status="uploaded",
        detected_mapping=mapping,
        missing_required_fields=missing_required_fields,
        validation_summary={},
    )
    db.add(import_run)
    db.flush()

    if missing_required_fields:
        for field_name in missing_required_fields:
            db.add(
                ValidationIssue(
                    import_id=import_run.id,
                    record_id=None,
                    row_index=None,
                    field_name=field_name,
                    issue_code="missing_required_field_group",
                    message=f"Groupe de colonnes requis introuvable: {field_name}.",
                    severity="error",
                )
            )
        _compute_summary(db, import_run)
        db.commit()
        db.refresh(import_run)
        return import_run

    records: list[EmployeeRecord] = []
    for index, row in dataframe.iterrows():
        raw_payload = _build_raw_payload(row, mapping)
        normalized = normalize_payload(raw_payload)
        records.append(
            EmployeeRecord(
                import_id=import_run.id,
                row_index=index + 2,
                raw_payload=raw_payload,
                normalized_payload={
                    key: value.isoformat() if isinstance(value, date) else value for key, value in normalized.items()
                },
                employee_id=normalized.get("employee_id"),
                full_name=normalized.get("full_name"),
                department=normalized.get("department"),
                gender=normalized.get("gender"),
                age=normalized.get("age"),
                birth_date=normalized.get("birth_date"),
                salary=normalized.get("salary"),
                hire_date=normalized.get("hire_date"),
                tenure_years=normalized.get("tenure_years"),
                training_hours=normalized.get("training_hours"),
                performance_score=normalized.get("performance_score"),
                satisfaction_score=normalized.get("satisfaction_score"),
                attrition=normalized.get("attrition"),
                is_valid=False,
            )
        )

    db.add_all(records)
    db.commit()
    db.refresh(import_run)
    revalidate_import(db, import_run)
    db.refresh(import_run)
    return import_run


def get_import_or_404(db: Session, import_id: int) -> ImportRun:
    import_run = db.get(ImportRun, import_id)
    if not import_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import introuvable.")
    return import_run


def list_imports(db: Session) -> list[ImportRun]:
    return db.query(ImportRun).order_by(ImportRun.uploaded_at.desc()).all()


def list_issues(db: Session, import_id: int, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    query = db.query(ValidationIssue).filter(ValidationIssue.import_id == import_id).order_by(
        ValidationIssue.row_index.asc(),
        ValidationIssue.id.asc(),
    )
    total = query.count()
    issues = query.offset((page - 1) * page_size).limit(page_size).all()
    items: list[dict[str, Any]] = []
    for issue in issues:
        current_value = None
        if issue.record and issue.field_name:
            current_value = getattr(issue.record, issue.field_name, None)
            if isinstance(current_value, date):
                current_value = current_value.isoformat()
        items.append(
            {
                "id": issue.id,
                "recordId": issue.record_id,
                "rowIndex": issue.row_index,
                "fieldName": issue.field_name,
                "issueCode": issue.issue_code,
                "message": issue.message,
                "severity": issue.severity,
                "currentValue": current_value,
            }
        )
    return items, total


def patch_record(db: Session, import_id: int, record_id: int, payload: dict[str, Any]) -> ImportRun:
    import_run = get_import_or_404(db, import_id)
    record = db.query(EmployeeRecord).filter(
        EmployeeRecord.import_id == import_id,
        EmployeeRecord.id == record_id,
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enregistrement introuvable.")

    merged_payload = dict(record.raw_payload or {})
    for key, value in payload.items():
        merged_payload[key] = value
    record.raw_payload = merged_payload
    db.commit()
    revalidate_import(db, import_run)
    db.refresh(import_run)
    return import_run


def activate_import(db: Session, import_id: int) -> ImportRun:
    import_run = get_import_or_404(db, import_id)
    if import_run.missing_required_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'activer un import avec des colonnes requises manquantes.",
        )

    unresolved_issues = db.query(func.count(ValidationIssue.id)).filter(ValidationIssue.import_id == import_id).scalar() or 0
    if unresolved_issues:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'activer un import tant que des incohérences bloquantes subsistent.",
        )

    db.query(ImportRun).update({ImportRun.is_active: False})
    import_run.is_active = True
    import_run.status = "active"
    db.commit()
    db.refresh(import_run)
    return import_run

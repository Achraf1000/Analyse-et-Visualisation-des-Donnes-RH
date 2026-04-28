from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ImportRun(Base):
    __tablename__ = "imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="uploaded")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    detected_mapping: Mapped[dict] = mapped_column(JSON, default=dict)
    missing_required_fields: Mapped[list] = mapped_column(JSON, default=list)
    validation_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    records: Mapped[list["EmployeeRecord"]] = relationship(
        back_populates="import_run",
        cascade="all, delete-orphan",
    )
    issues: Mapped[list["ValidationIssue"]] = relationship(
        back_populates="import_run",
        cascade="all, delete-orphan",
    )
    model_runs: Mapped[list["ModelRun"]] = relationship(
        back_populates="import_run",
        cascade="all, delete-orphan",
    )


class EmployeeRecord(Base):
    __tablename__ = "employee_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("imports.id"), nullable=False, index=True)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    employee_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    gender: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    age: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tenure_years: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    training_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    performance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    satisfaction_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    attrition: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    risk_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    normalized_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    import_run: Mapped["ImportRun"] = relationship(back_populates="records")
    issues: Mapped[list["ValidationIssue"]] = relationship(
        back_populates="record",
        cascade="all, delete-orphan",
    )


class ValidationIssue(Base):
    __tablename__ = "validation_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("imports.id"), nullable=False, index=True)
    record_id: Mapped[int | None] = mapped_column(ForeignKey("employee_records.id"), nullable=True, index=True)
    row_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    field_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issue_code: Mapped[str] = mapped_column(String(128), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="error")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    import_run: Mapped["ImportRun"] = relationship(back_populates="issues")
    record: Mapped["EmployeeRecord"] = relationship(back_populates="issues")


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("imports.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), default="trained")
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    artifact_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    coefficients: Mapped[list] = mapped_column(JSON, default=list)
    confusion_matrix: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)

    import_run: Mapped["ImportRun"] = relationship(back_populates="model_runs")

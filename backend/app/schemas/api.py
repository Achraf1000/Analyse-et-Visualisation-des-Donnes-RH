from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class CurrentUserResponse(BaseModel):
    id: int
    email: str
    full_name: str = Field(alias="fullName")
    role: str

    model_config = ConfigDict(populate_by_name=True)


class TokenResponse(BaseModel):
    access_token: str = Field(alias="accessToken")
    token_type: str = Field(alias="tokenType", default="bearer")
    user: CurrentUserResponse

    model_config = ConfigDict(populate_by_name=True)


class ValidationSummary(BaseModel):
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    blocking_issues: int = 0
    warning_issues: int = 0


class ImportResponse(BaseModel):
    import_id: int = Field(alias="importId")
    filename: str
    status: str
    is_active: bool = Field(alias="isActive")
    uploaded_at: datetime = Field(alias="uploadedAt")
    detected_mapping: dict[str, str | None] = Field(alias="detectedMapping")
    missing_required_fields: list[str] = Field(alias="missingRequiredFields")
    validation_summary: ValidationSummary = Field(alias="validationSummary")

    model_config = ConfigDict(populate_by_name=True)


class ImportListResponse(BaseModel):
    items: list[ImportResponse]


class ImportDetailResponse(ImportResponse):
    total_rows: int = Field(alias="totalRows")
    valid_rows: int = Field(alias="validRows")
    invalid_rows: int = Field(alias="invalidRows")

    model_config = ConfigDict(populate_by_name=True)


class ValidationIssueResponse(BaseModel):
    id: int
    record_id: int | None = Field(alias="recordId")
    row_index: int | None = Field(alias="rowIndex")
    field_name: str | None = Field(alias="fieldName")
    issue_code: str = Field(alias="issueCode")
    message: str
    severity: str
    current_value: Any = Field(alias="currentValue", default=None)

    model_config = ConfigDict(populate_by_name=True)


class IssuesResponse(BaseModel):
    items: list[ValidationIssueResponse]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)


class KPIResponse(BaseModel):
    headcount: int
    turnover_rate: float = Field(alias="turnoverRate")
    average_tenure: float = Field(alias="averageTenure")
    average_salary: float = Field(alias="averageSalary")
    total_cost: float = Field(alias="totalCost")

    model_config = ConfigDict(populate_by_name=True)


class ScatterSeriesPoint(BaseModel):
    employee_id: str = Field(alias="employeeId")
    x: float
    y: float
    attrition: int
    department: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CorrelationResponse(BaseModel):
    labels: list[str]
    matrix: list[list[float]]
    scatter_series: dict[str, list[ScatterSeriesPoint]] = Field(alias="scatterSeries")
    insights: list[str]

    model_config = ConfigDict(populate_by_name=True)


class ModelMetricsResponse(BaseModel):
    accuracy: float
    precision: float
    recall: float
    roc_auc: float = Field(alias="rocAuc")

    model_config = ConfigDict(populate_by_name=True)


class CoefficientResponse(BaseModel):
    feature: str
    coefficient: float


class ModelRunResponse(BaseModel):
    model_run_id: int = Field(alias="modelRunId")
    trained_at: datetime = Field(alias="trainedAt")
    metrics: ModelMetricsResponse
    confusion_matrix: list[list[int]] = Field(alias="confusionMatrix")
    coefficients: list[CoefficientResponse]

    model_config = ConfigDict(populate_by_name=True)


class PredictionRecordResponse(BaseModel):
    record_id: int = Field(alias="recordId")
    employee_id: str = Field(alias="employeeId")
    full_name: str | None = Field(alias="fullName")
    department: str | None = None
    gender: str | None = None
    tenure_years: float | None = Field(alias="tenureYears")
    performance_score: float | None = Field(alias="performanceScore")
    satisfaction_score: float | None = Field(alias="satisfactionScore")
    salary: float | None = None
    risk_probability: float = Field(alias="riskProbability")
    risk_level: str = Field(alias="riskLevel")

    model_config = ConfigDict(populate_by_name=True)


class PredictionsResponse(BaseModel):
    model_run: ModelRunResponse | None = Field(alias="modelRun")
    items: list[PredictionRecordResponse]

    model_config = ConfigDict(populate_by_name=True)


class DashboardChartBucket(BaseModel):
    name: str
    value: float
    secondary_value: float | None = Field(alias="secondaryValue", default=None)

    model_config = ConfigDict(populate_by_name=True)


class DashboardResponse(BaseModel):
    kpis: KPIResponse
    filters: dict[str, list[str]]
    charts: dict[str, list[DashboardChartBucket]]
    meta: dict[str, Any]


class HealthResponse(BaseModel):
    status: str

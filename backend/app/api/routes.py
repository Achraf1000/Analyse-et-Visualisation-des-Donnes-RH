from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.api import (
    CorrelationResponse,
    DashboardResponse,
    HealthResponse,
    ImportDetailResponse,
    ImportListResponse,
    ImportResponse,
    IssuesResponse,
    ModelRunResponse,
    PredictionsResponse,
)
from app.services.analytics import get_correlation_payload, get_dashboard_payload, get_kpi_payload, get_predictions_payload
from app.services.imports import activate_import, create_import_from_csv, get_import_or_404, list_imports, list_issues, patch_record, serialize_import
from app.services.ml import train_attrition_model
from app.services.reporting import generate_pdf_report


router = APIRouter(prefix="/api")


def _filters(
    department: str | None = Query(default=None),
    gender: str | None = Query(default=None),
    tenure_min: float | None = Query(default=None, alias="tenureMin"),
    tenure_max: float | None = Query(default=None, alias="tenureMax"),
    age_min: float | None = Query(default=None, alias="ageMin"),
    age_max: float | None = Query(default=None, alias="ageMax"),
):
    return {
        "department": department,
        "gender": gender,
        "tenure_min": tenure_min,
        "tenure_max": tenure_max,
        "age_min": age_min,
        "age_max": age_max,
    }


@router.get("/health", response_model=HealthResponse)
def healthcheck():
    return {"status": "ok"}


@router.post("/imports/csv", response_model=ImportResponse)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    created = await create_import_from_csv(db, file)
    return serialize_import(created)


@router.get("/imports", response_model=ImportListResponse)
def get_imports(db: Session = Depends(get_db)):
    return {"items": [serialize_import(import_run) for import_run in list_imports(db)]}


@router.get("/imports/{import_id}", response_model=ImportDetailResponse)
def get_import(import_id: int, db: Session = Depends(get_db)):
    return serialize_import(get_import_or_404(db, import_id))


@router.get("/imports/{import_id}/issues", response_model=IssuesResponse)
def get_import_issues(
    import_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200, alias="pageSize"),
    db: Session = Depends(get_db),
):
    items, total = list_issues(db, import_id, page, page_size)
    return {"items": items, "total": total, "page": page, "pageSize": page_size}


@router.patch("/imports/{import_id}/records/{record_id}", response_model=ImportResponse)
def update_record(import_id: int, record_id: int, payload: dict, db: Session = Depends(get_db)):
    updated_import = patch_record(db, import_id, record_id, payload)
    return serialize_import(updated_import)


@router.post("/imports/{import_id}/activate", response_model=ImportResponse)
def activate_selected_import(import_id: int, db: Session = Depends(get_db)):
    activated = activate_import(db, import_id)
    return serialize_import(activated)


@router.get("/kpis")
def get_kpis(filters: dict = Depends(_filters), db: Session = Depends(get_db)):
    return get_kpi_payload(db, **filters)


@router.get("/analytics/correlations", response_model=CorrelationResponse)
def correlations(filters: dict = Depends(_filters), db: Session = Depends(get_db)):
    return get_correlation_payload(db, **filters)


@router.post("/models/attrition/train", response_model=ModelRunResponse)
def train_model(db: Session = Depends(get_db)):
    return train_attrition_model(db)


@router.get("/models/attrition/predictions", response_model=PredictionsResponse)
def predictions(filters: dict = Depends(_filters), db: Session = Depends(get_db)):
    return get_predictions_payload(db, **filters)


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(filters: dict = Depends(_filters), db: Session = Depends(get_db)):
    return get_dashboard_payload(db, **filters)


@router.get("/reports/pdf")
def pdf_report(filters: dict = Depends(_filters), db: Session = Depends(get_db)):
    dashboard_payload = get_dashboard_payload(db, **filters)
    correlation_payload = get_correlation_payload(db, **filters)
    pdf_bytes = generate_pdf_report(filters, dashboard_payload, correlation_payload)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="rapport-rh.pdf"'},
    )

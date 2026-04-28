from io import BytesIO

from fastapi.testclient import TestClient

from app.db.session import Base, SessionLocal, engine
from app.main import app
from app.services.auth import seed_demo_users


client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_users(db)
    finally:
        db.close()


def auth_headers(email: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


def admin_headers() -> dict[str, str]:
    return auth_headers("admin.rh@demo.local", "Admin123!")


def manager_headers() -> dict[str, str]:
    return auth_headers("manager.rh@demo.local", "Manager123!")


def analyste_headers() -> dict[str, str]:
    return auth_headers("analyste.rh@demo.local", "Analyste123!")


def dirigeant_headers() -> dict[str, str]:
    return auth_headers("dirigeant.rh@demo.local", "Dirigeant123!")


def valid_csv_content() -> str:
    return """employee_id,department,gender,age,salary,hire_date,training_hours,performance_score,satisfaction_score,attrition,full_name
E001,Finance,F,31,3200,2018-01-10,20,4,4,0,Alice Martin
E002,Finance,M,45,4200,2014-03-12,12,3,2,1,Marc Dupont
E003,IT,F,29,3900,2020-08-01,35,5,5,0,Lina Moreau
E004,IT,M,38,4600,2016-06-11,10,2,2,1,Paul Bernard
E005,HR,F,41,3500,2015-05-16,18,4,3,0,Sarah Petit
E006,HR,M,27,2800,2022-02-20,25,5,4,0,Leo Simon
E007,Sales,F,36,4100,2017-11-05,8,2,1,1,Emma Roux
E008,Sales,M,33,3700,2019-09-13,16,3,2,1,Tom Leroy
E009,Operations,F,30,3400,2021-04-18,22,4,4,0,Nina Rey
E010,Operations,M,44,4400,2013-07-07,6,2,2,1,Hugo Noel
"""


def create_and_activate_dataset() -> int:
    response = client.post(
        "/api/imports/csv",
        headers=admin_headers(),
        files={"file": ("valid.csv", BytesIO(valid_csv_content().encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 200
    import_id = response.json()["importId"]
    activate_response = client.post(f"/api/imports/{import_id}/activate", headers=admin_headers())
    assert activate_response.status_code == 200
    return import_id


def test_login_and_me():
    login_response = client.post(
        "/api/auth/login",
        json={"email": "manager.rh@demo.local", "password": "Manager123!"},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["tokenType"] == "bearer"
    assert body["user"]["role"] == "MANAGER_RH"

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['accessToken']}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "manager.rh@demo.local"


def test_login_invalid_credentials():
    response = client.post(
        "/api/auth/login",
        json={"email": "manager.rh@demo.local", "password": "wrong"},
    )
    assert response.status_code == 401


def test_protected_routes_require_token_and_role():
    assert client.get("/api/imports").status_code == 401
    assert client.post("/api/models/attrition/train", headers=admin_headers()).status_code == 403


def test_dashboard_requires_active_import_for_manager():
    response = client.get("/api/dashboard", headers=manager_headers())
    assert response.status_code == 409
    assert response.json()["detail"] == "Aucun import actif. Activez un dataset valide pour poursuivre."


def test_import_requires_missing_columns():
    content = "employee_id,department\n1,Finance\n"
    response = client.post(
        "/api/imports/csv",
        headers=admin_headers(),
        files={"file": ("missing.csv", BytesIO(content.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert "salary" in body["missingRequiredFields"]


def test_import_activate_train_and_role_flow():
    import_id = create_and_activate_dataset()

    imports_response = client.get("/api/imports", headers=analyste_headers())
    assert imports_response.status_code == 200
    assert imports_response.json()["items"][0]["importId"] == import_id

    kpis_response = client.get("/api/kpis", headers=manager_headers())
    assert kpis_response.status_code == 200
    assert kpis_response.json()["headcount"] == 10

    train_response = client.post("/api/models/attrition/train", headers=manager_headers())
    assert train_response.status_code == 200
    assert "metrics" in train_response.json()

    predictions_response = client.get("/api/models/attrition/predictions", headers=manager_headers())
    assert predictions_response.status_code == 200
    assert len(predictions_response.json()["items"]) == 10

    correlations_response = client.get("/api/analytics/correlations", headers=analyste_headers())
    assert correlations_response.status_code == 200
    assert "matrix" in correlations_response.json()

    filters_response = client.get("/api/filters", headers=analyste_headers())
    assert filters_response.status_code == 200
    assert "Finance" in filters_response.json()["departments"]

    dashboard_response = client.get("/api/dashboard", headers=dirigeant_headers())
    assert dashboard_response.status_code == 200
    assert "charts" in dashboard_response.json()

    pdf_response = client.get("/api/reports/pdf", headers=dirigeant_headers())
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"


def test_import_example_attrition_dataset_columns():
    content = """EmpID,Age,AgeGroup,Attrition,BusinessTravel,DailyRate,Department,DistanceFromHome,Education,EducationField,EmployeeCount,EmployeeNumber,EnvironmentSatisfaction,Gender,HourlyRate,JobInvolvement,JobLevel,JobRole,JobSatisfaction,MaritalStatus,MonthlyIncome,SalarySlab,MonthlyRate,NumCompaniesWorked,Over18,OverTime,PercentSalaryHike,PerformanceRating,RelationshipSatisfaction,StandardHours,StockOptionLevel,TotalWorkingYears,TrainingTimesLastYear,WorkLifeBalance,YearsAtCompany,YearsInCurrentRole,YearsSinceLastPromotion,YearsWithCurrManager
RM297,18,18-25,Yes,Travel_Rarely,230,Sales,3,3,Marketing,1,405,3,Female,54,3,1,Sales Executive,3,Single,1420,Upto 5k,25233,1,Y,No,13,3,3,80,0,0,3,3,0,0,0,0
RM302,19,18-25,No,Travel_Rarely,489,Research & Development,1,1,Technical Degree,1,410,2,Male,67,3,1,Laboratory Technician,1,Married,2796,Upto 5k,12464,1,Y,No,12,3,3,80,0,1,3,3,1,0,0,0
RM458,20,18-25,Yes,Travel_Rarely,1097,Research & Development,11,3,Medical,1,569,3,Male,82,3,1,Laboratory Technician,3,Single,2678,Upto 5k,16553,1,Y,Yes,11,3,3,80,0,1,2,1,1,0,0,1
RM728,21,18-25,No,Travel_Frequently,391,Sales,7,3,Life Sciences,1,909,4,Female,43,3,1,Sales Representative,3,Married,2326,Upto 5k,19281,1,Y,No,14,4,3,80,0,2,3,2,1,0,0,1
RM829,22,18-25,Yes,Non-Travel,534,Research & Development,15,3,Life Sciences,1,1021,2,Female,59,3,1,Research Scientist,2,Single,2871,Upto 5k,23785,1,Y,Yes,15,3,2,80,0,2,3,2,2,1,0,1
RM940,23,18-25,No,Travel_Rarely,427,Human Resources,7,3,Human Resources,1,1152,3,Male,83,3,1,Human Resources,4,Single,2935,Upto 5k,12340,1,Y,No,13,3,4,80,0,2,3,3,2,1,0,1
RM1044,24,18-25,No,Travel_Rarely,673,Research & Development,8,2,Medical,1,1270,4,Female,92,3,1,Research Scientist,3,Divorced,3120,Upto 5k,15420,2,Y,No,16,4,3,80,1,4,4,4,3,1,0,2
RM1168,25,18-25,Yes,Travel_Frequently,599,Sales,2,3,Marketing,1,1410,2,Male,70,3,2,Sales Executive,2,Single,3550,Upto 5k,14555,2,Y,Yes,17,4,2,80,0,5,2,2,4,3,1,2
"""
    response = client.post(
        "/api/imports/csv",
        headers=admin_headers(),
        files={"file": ("example-attrition.csv", BytesIO(content.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["missingRequiredFields"] == []
    assert body["validationSummary"]["invalid_rows"] == 0
    assert body["detectedMapping"]["employee_id"] == "EmpID"
    assert body["detectedMapping"]["salary"] == "MonthlyIncome"
    assert body["detectedMapping"]["tenure_years"] == "YearsAtCompany"
    assert body["detectedMapping"]["training_hours"] == "TrainingTimesLastYear"
    assert body["detectedMapping"]["performance_score"] == "PerformanceRating"
    assert body["detectedMapping"]["satisfaction_score"] == "JobSatisfaction"

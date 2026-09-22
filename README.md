HR Analytics & Employee Attrition Modeling

Academic full-stack project developed as part of my engineering studies at Polytech-Intl, Tunis.

The application turns CSV employee records into validated datasets, interactive HR dashboards, correlation analysis and an interpretable machine-learning model. It connects data preparation, analysis, modeling and reporting within a role-based web application.

Core stack: React · FastAPI · pandas · scikit-learn · SQLAlchemy · SQLite

Project objectives

Build a complete workflow from raw data import to analytical reporting.

Detect and correct data-quality issues before analysis.

Explore relationships between satisfaction, performance, training, tenure and attrition.

Integrate a supervised-learning model into a web application.

Provide different interfaces and permissions for HR administrators, analysts, managers and executives.

Features

Module

Implemented functionality

Data import

CSV upload, delimiter detection, column mapping and import history

Data quality

Missing-field checks, duplicate employee identifiers, range validation and record correction

Dataset management

Activation of a validated import as the shared dataset for analysis

Dashboard

Record count, attrition share, average tenure, average salary and total recorded salaries

Visualization

Department, gender, tenure and risk distributions; shared filters

Exploratory analysis

Correlation heatmap and scatter plots for selected HR variables

Machine learning

Logistic regression, evaluation metrics, model coefficients and probability-based risk groups

Reporting

PDF export of the filtered analysis

Access control

JWT authentication, password hashing and role checks in the API and frontend

The interface is in French.

Roles and demonstration accounts

Accounts are created automatically when the application starts with an empty user table.

Role

Email

Demo password

Main access

HR administrator

admin.rh@demo.local

Admin123!

Import, correct and activate datasets

HR analyst

analyste.rh@demo.local

Analyste123!

Correlations and exploratory analysis

HR manager

manager.rh@demo.local

Manager123!

Dashboard, model training and prediction results

Executive

dirigeant.rh@demo.local

Dirigeant123!

Dashboard and PDF reports

These are local demonstration accounts with intentionally public credentials. The application currently seeds them automatically; replace this behavior before hosting an accessible instance.

Technology stack

Layer

Technologies

Frontend

React 19, JavaScript, Vite, React Router

Client data and tables

TanStack Query, TanStack Table

Interactive charts

Recharts

Backend

Python, FastAPI, Pydantic, Uvicorn

Persistence

SQLAlchemy, SQLite by default

Data processing

pandas

Machine learning

scikit-learn, joblib

Report charts

Matplotlib, Seaborn

PDF generation

WeasyPrint, with a simplified ReportLab fallback

Authentication

JWT with python-jose, password hashing with bcrypt

Tests and checks

pytest, HTTPX, Vitest, React Testing Library, ESLint

Architecture

flowchart TD
    UI["React web application"] --> API["FastAPI API and role checks"]
    API --> IMPORT["CSV validation and correction"]
    API --> ANALYSIS["Analytics and model training"]
    API --> REPORT["PDF reporting"]
    IMPORT --> DB[("SQLite database")]
    ANALYSIS --> DB
    REPORT --> DB
    ANALYSIS --> MODEL["Saved model artifacts"]

The backend separates routing, schemas, persistence and business services. The frontend organizes its screens around imports, dashboards, analytics, predictions and reports.

Machine-learning approach

The current model is a scikit-learn pipeline using:

StandardScaler for numeric variables;

OneHotEncoder(handle_unknown="ignore") for categorical variables;

LogisticRegression(max_iter=500) for binary classification.

Numeric inputs are age, salary, tenure, training hours, performance and satisfaction. Categorical inputs are department and gender. The target is attrition, where 1 denotes a departure and 0 denotes no departure in the source dataset.

Training uses a stratified split with random_state=42. The test share is 25% for datasets with at least 12 records and 40% for smaller accepted datasets.

Evaluation returns accuracy, precision, recall, ROC AUC and a confusion matrix. The application also exposes model coefficients and saves the trained pipeline with joblib.

Displayed risk groups use the implemented thresholds:

Probability

Group

Below 0.33

Low

0.33 through 0.66

Medium

Above 0.66

High

Metrics depend on the imported dataset; no fixed accuracy score is claimed. Scores displayed for the complete active dataset include training records, while evaluation metrics use the held-out test subset.

Run locally

Prerequisites

Windows x64 and PowerShell for the instructions below.

Python 3.11.

Node.js 22.12 or later within the Node.js 22 release line, and npm.

Git.

The current frontend manifest directly includes Windows-specific native packages. Linux and macOS installation needs dependency cleanup before these instructions can be considered portable.

1. Clone the repository

git clone https://github.com/Achraf1000/Analyse-et-Visualisation-des-Donn-es-RH.git
cd Analyse-et-Visualisation-des-Donn-es-RH

2. Start the backend

cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SECRET_KEY = (.\venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))")
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

The application creates its SQLite database and tables automatically. No external database server is required for the default configuration.

API documentation: http://127.0.0.1:8000/docs

Health endpoint: http://127.0.0.1:8000/api/health

Backend configuration reads process environment variables: DATABASE_URL, SECRET_KEY, JWT_ALGORITHM and ACCESS_TOKEN_EXPIRE_MINUTES. It does not automatically load a backend .env file.

3. Start the frontend

In another terminal, from the repository root:

cd frontend
npm ci
npm run dev -- --port 5173 --strictPort

Open http://localhost:5173. The Vite development proxy forwards /api requests to the backend on port 8000.

4. Explore the application

Sign in as the HR administrator.

Upload a CSV, review validation issues and activate the valid import.

Sign out and sign in as the HR analyst to explore correlations.

Sign in as the HR manager to view the dashboard and train the attrition model.

Sign in as the executive to export a PDF report.

WeasyPrint produces the report with charts when its native dependencies are available. If WeasyPrint cannot be imported, the implemented ReportLab fallback produces a simpler text report.

CSV input

A minimal canonical header is:

employee_id,department,gender,age,salary,tenure_years,training_hours,performance_score,satisfaction_score,attrition

The importer also recognizes several French and English aliases. birth_date can replace age, and hire_date can replace tenure_years. full_name is optional.

Validation includes:

unique, non-empty employee identifiers;

department and gender values;

age between 16 and 75;

positive salary and non-negative tenure and training values;

performance and satisfaction scores between 1 and 5;

a binary attrition label.

For a local demonstration, save this invented dataset as demo_hr.csv and import it:

employee_id,department,gender,age,salary,tenure_years,training_hours,performance_score,satisfaction_score,attrition
DEMO001,Finance,F,31,3200,5,20,4,4,0
DEMO002,Finance,M,45,4200,8,12,3,2,1
DEMO003,IT,F,29,3900,3,35,5,5,0
DEMO004,IT,M,38,4600,6,10,2,2,1
DEMO005,HR,F,41,3500,7,18,4,3,0
DEMO006,HR,M,27,2800,2,25,5,4,0
DEMO007,Sales,F,36,4100,4,8,2,1,1
DEMO008,Sales,M,33,3700,5,16,3,2,1
DEMO009,Operations,F,30,3400,3,22,4,4,0
DEMO010,Operations,M,44,4400,9,6,2,2,1
DEMO011,IT,F,26,3100,1,30,4,4,0
DEMO012,Finance,M,39,4300,6,9,3,2,1

This small synthetic dataset exercises the workflow; its results are not evidence of predictive performance. No external dataset is downloaded automatically.

Tests

The repository includes backend tests for authentication, permissions, import validation, dataset activation, training, analytics and PDF export, plus frontend tests.

Run backend tests in a separate terminal from backend/ with a dedicated test database:

$env:DATABASE_URL = "sqlite:///./data/hr_analytics_test.db"
.\venv\Scripts\python.exe -m pytest -q

The current test setup drops and recreates tables in its configured database. Keep the test database separate from your demonstration data.

From frontend/:

npm test
npm run lint
npm run build

These are the repository's verification commands, not a statement that they have passed in every environment.

Code guide

Path

Purpose

backend/app/api/routes.py

API endpoints and role restrictions

backend/app/services/imports.py

CSV parsing, normalization, validation and corrections

backend/app/services/analytics.py

Indicators, filters and correlations

backend/app/services/ml.py

Training, evaluation and model persistence

backend/app/services/reporting.py

PDF report generation

backend/app/services/auth.py

Login, tokens, demo accounts and access control

frontend/src/pages

User-facing application screens

backend/tests and frontend/src/test

Existing automated tests

Academic scope and next steps

This project demonstrates an end-to-end data application. It is an educational prototype, not a validated system for employment decisions.

The dashboard's attrition percentage is the share of departed records in the active dataset, not an annual turnover rate. Salary aggregates reflect the units supplied in the CSV.

The current model scores records from the active labeled dataset. Future improvements include inference on new unlabeled records, cross-validation, model comparison, probability calibration and fairness evaluation. Age and gender are currently included as features and would require particular scrutiny before any real-world use.

Additional engineering improvements include cross-platform dependency cleanup, continuous integration and replacement of demonstration authentication settings before deployment.

Skills demonstrated

Full-stack integration of a React interface and Python REST API.

Data normalization, validation and quality control.

Exploratory analysis and interactive data visualization.

Supervised-learning pipelines and model evaluation.

Relational persistence and role-based access.

Automated reporting and application testing.

Author

Achraf Abdelhedi · Engineering student at Polytech-Intl

GitHub

LinkedIn

Email


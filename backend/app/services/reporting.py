from __future__ import annotations

import base64
import io
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from fastapi import HTTPException, status

matplotlib.use("Agg")

try:  # pragma: no cover
    from weasyprint import HTML
except Exception:  # pragma: no cover
    HTML = None

try:  # pragma: no cover
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover
    canvas = None
    A4 = None


def _chart_to_base64(figure) -> str:
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", bbox_inches="tight", dpi=150)
    plt.close(figure)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def _build_department_chart(department_data: list[dict]) -> str:
    figure, axis = plt.subplots(figsize=(6, 3))
    names = [item["name"] for item in department_data] or ["Aucune donnée"]
    values = [item["value"] for item in department_data] or [0]
    axis.bar(names, values, color="#0f766e")
    axis.set_title("Effectif par département")
    axis.set_ylabel("Employés")
    axis.tick_params(axis="x", rotation=20)
    return _chart_to_base64(figure)


def _build_risk_chart(risk_data: list[dict]) -> str:
    figure, axis = plt.subplots(figsize=(5, 3))
    labels = [item["name"] for item in risk_data] or ["Non évalué"]
    values = [item["value"] for item in risk_data] or [1]
    axis.pie(values, labels=labels, autopct="%1.0f%%", colors=["#22c55e", "#f59e0b", "#ef4444", "#94a3b8"])
    axis.set_title("Distribution du risque de départ")
    return _chart_to_base64(figure)


def _build_correlation_chart(correlation_payload: dict) -> str:
    figure, axis = plt.subplots(figsize=(6, 4))
    sns.heatmap(
        correlation_payload["matrix"],
        annot=True,
        fmt=".2f",
        cmap="crest",
        xticklabels=correlation_payload["labels"],
        yticklabels=correlation_payload["labels"],
        ax=axis,
    )
    axis.set_title("Matrice de corrélation")
    return _chart_to_base64(figure)


def _build_html(filters: dict, dashboard_payload: dict, correlation_payload: dict) -> str:
    department_chart = _build_department_chart(dashboard_payload["charts"]["departmentHeadcount"])
    risk_chart = _build_risk_chart(dashboard_payload["charts"]["riskDistribution"])
    correlation_chart = _build_correlation_chart(correlation_payload)
    filter_labels = [
        f"{label}: {value}"
        for label, value in {
            "Département": filters.get("department") or "Tous",
            "Sexe": filters.get("gender") or "Tous",
            "Ancienneté min": filters.get("tenure_min", "N/A"),
            "Ancienneté max": filters.get("tenure_max", "N/A"),
            "Âge min": filters.get("age_min", "N/A"),
            "Âge max": filters.get("age_max", "N/A"),
        }.items()
    ]
    kpis = dashboard_payload["kpis"]
    insights = "".join(f"<li>{insight}</li>" for insight in correlation_payload["insights"])
    return f"""
    <html>
      <head>
        <style>
          body {{
            font-family: Arial, sans-serif;
            color: #0f172a;
            margin: 28px;
          }}
          h1, h2 {{
            color: #0f766e;
          }}
          .cards {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin: 16px 0 24px;
          }}
          .card {{
            padding: 12px;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            background: #f8fafc;
          }}
          .charts {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
          }}
          img {{
            width: 100%;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
          }}
          ul {{
            padding-left: 18px;
          }}
          .filters {{
            margin: 12px 0 24px;
            font-size: 13px;
            color: #334155;
          }}
        </style>
      </head>
      <body>
        <h1>Rapport analytique RH</h1>
        <p>Export généré le {datetime.now().strftime("%d/%m/%Y %H:%M")}.</p>
        <div class="filters">{' | '.join(filter_labels)}</div>
        <div class="cards">
          <div class="card"><strong>Effectif</strong><div>{kpis['headcount']}</div></div>
          <div class="card"><strong>Turnover</strong><div>{kpis['turnoverRate']}%</div></div>
          <div class="card"><strong>Ancienneté moyenne</strong><div>{kpis['averageTenure']} ans</div></div>
          <div class="card"><strong>Coût RH total</strong><div>{kpis['totalCost']:.2f}</div></div>
        </div>
        <h2>Visualisations</h2>
        <div class="charts">
          <img src="data:image/png;base64,{department_chart}" />
          <img src="data:image/png;base64,{risk_chart}" />
        </div>
        <h2>Corrélations</h2>
        <img src="data:image/png;base64,{correlation_chart}" />
        <h2>Synthèse</h2>
        <ul>{insights}</ul>
      </body>
    </html>
    """


def generate_pdf_report(filters: dict, dashboard_payload: dict, correlation_payload: dict) -> bytes:
    html = _build_html(filters, dashboard_payload, correlation_payload)
    if HTML is not None:
        return HTML(string=html).write_pdf()

    if canvas is None or A4 is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Aucun moteur PDF disponible sur cette machine.",
        )

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, 800, "Rapport analytique RH")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 780, f"Export généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y = 740
    for key, value in dashboard_payload["kpis"].items():
        pdf.drawString(50, y, f"{key}: {value}")
        y -= 18
    pdf.drawString(50, y - 10, "Visualisations indisponibles dans le fallback PDF.")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.read()

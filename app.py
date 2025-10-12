# app.py
import tempfile
from typing import List, Dict, Any
import gradio as gr
import pandas as pd

from core import estimate_all, DISCLAIMER

# Optional PDF export (uses reportlab like your Flask route)
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

TASKS = [
    "lagging/insulation",
    "maintenance/demolition",
    "cement/board cutting",
    "garage/brakes",
    "bystander",
]
ERAS = ["pre-1980", "1980-1999", "2000+"]

DEFAULT_ROWS = [
    {
        "task": "bystander",
        "era": "1980-1999",
        "start_year": 1985,
        "end_year": 1990,
        "days_per_week": 5,
        "hours_per_day": 6,
        "rpe": False,
        "lev": False,
    }
]

COLUMNS = [
    ("task", "category"),
    ("era", "category"),
    ("start_year", "number"),
    ("end_year", "number"),
    ("days_per_week", "number"),
    ("hours_per_day", "number"),
    ("rpe", "bool"),
    ("lev", "bool"),
]

def _df_to_roles(df: pd.DataFrame) -> List[Dict[str, Any]]:
    # Coerce and drop empty rows
    roles: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        if pd.isna(row.get("task")) or pd.isna(row.get("era")):
            continue
        try:
            roles.append({
                "task": str(row["task"]).strip(),
                "era": str(row["era"]).strip(),
                "start_year": int(row["start_year"]),
                "end_year": int(row["end_year"]),
                "days_per_week": float(row["days_per_week"]),
                "hours_per_day": float(row["hours_per_day"]),
                "rpe": bool(row["rpe"]),
                "lev": bool(row["lev"]),
            })
        except Exception:
            # Skip malformed row
            continue
    return roles

def predict(df: pd.DataFrame):
    roles = _df_to_roles(df)
    if not roles:
        return (
            gr.update(value=None),
            gr.update(value=None),
            "Add at least one valid role row.",
            pd.DataFrame(),
        )
    result = estimate_all(roles)
    summaries_df = pd.DataFrame(result["summaries"])
    note = f"Latency (years since first exposure): ~{result['latency_years']}" if result["latency_years"] is not None else "Latency: n/a"
    totals = f"{result['total_low']}–{result['total_high']} f/ml·years"
    return result["total_low"], result["total_high"], note, summaries_df

def make_pdf(df: pd.DataFrame, totals_low, totals_high, latency_note: str):
    roles = _df_to_roles(df)
    if not roles:
        return None

    # Build PDF to a temp file and return its path
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    path = tmp.name
    tmp.close()

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(path, pagesize=A4)
    elems = []

    elems.append(Paragraph("<b>Asbestos Exposure Educational Estimator — Summary</b>", styles["Title"]))
    elems.append(Spacer(1, 12))

    for i, r in enumerate(roles, start=1):
        elems.append(Paragraph(f"<b>Role {i}:</b> {r['task']} ({r['era']}) {r['start_year']}–{r['end_year']}", styles["BodyText"]))
        elems.append(Paragraph(
            f"Days/week: {r['days_per_week']}, Hours/day: {r['hours_per_day']}, RPE: {bool(r['rpe'])}, LEV: {bool(r['lev'])}",
            styles["BodyText"]
        ))
        elems.append(Spacer(1, 6))

    elems.append(Spacer(1, 6))
    elems.append(Paragraph(
        f"<b>Cumulative exposure (f/ml·years):</b> {totals_low}–{totals_high}",
        styles["Heading2"]
    ))
    elems.append(Paragraph(f"<b>{latency_note}</b>", styles["BodyText"]))
    elems.append(Spacer(1, 12))

    interp = [
        ["Educational context (not diagnostic)"],
        ["• Asbestosis/Diffuse pleural thickening often associated with ~10–25+ f/ml·years."],
        ["• Lung cancer without asbestosis: typically very high cumulative exposures."],
        ["• Mesothelioma: no safe threshold; qualitative exposure history remains important."],
    ]
    table = Table(interp, colWidths=[480])
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), colors.lightgrey),
        ("BOX",(0,0),(-1,-1),0.5,colors.black),
        ("INNERGRID",(0,0),(-1,-1),0.25,colors.grey)
    ]))
    elems.append(table)
    elems.append(Spacer(1, 12))
    elems.append(Paragraph("<b>Disclaimer</b>", styles["Heading3"]))
    elems.append(Paragraph(DISCLAIMER, styles["BodyText"]))

    doc.build(elems)
    return path

with gr.Blocks(title="Asbestos Exposure Estimator") as demo:
    gr.Markdown("## Asbestos Exposure Estimator (Educational)\nEnter one or more roles, then click **Estimate**.")

    df = gr.Dataframe(
        headers=[c[0] for c in COLUMNS],
        datatype=[c[1] for c in COLUMNS],
        value=pd.DataFrame(DEFAULT_ROWS),
        wrap=True,
        row_count=(1, "dynamic"),
        col_count=(len(COLUMNS), "fixed"),
        label="Exposure roles",
    )

    with gr.Row():
        total_low = gr.Number(label="Total low (f/ml·years)", interactive=False)
        total_high = gr.Number(label="Total high (f/ml·years)", interactive=False)

    latency_text = gr.Textbox(label="Latency", interactive=False)
    summaries = gr.Dataframe(label="Per-role summaries (computed)", interactive=False)

    with gr.Row():
        btn = gr.Button("Estimate", variant="primary")
        pdf_btn = gr.Button("Export PDF")

    pdf_file = gr.File(label="Download PDF")

    btn.click(predict, inputs=[df], outputs=[total_low, total_high, latency_text, summaries])
    pdf_btn.click(make_pdf, inputs=[df, total_low, total_high, latency_text], outputs=[pdf_file])

    gr.Markdown(
        "> **Disclaimer:** " + DISCLAIMER
    )

if __name__ == "__main__":
    demo.launch()

from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from flask import Flask, render_template, request, jsonify
from pathlib import Path
import os
import logging
import traceback                 

@app.get("/_diag")
def _diag():
    tpl_dir = Path(app.template_folder)
    return jsonify({
        "app_file_dir": str(Path(__file__).resolve().parent),
        "template_folder": str(app.template_folder),
        "templates_exists": tpl_dir.exists(),
        "templates_listing": sorted(os.listdir(tpl_dir)) if tpl_dir.exists() else [],
    }), 200

logging.basicConfig(level=logging.INFO)

@app.before_first_request
def startup_note():
    p = Path(app.template_folder) / "index.html"
    app.logger.info(
        f"[startup] templates dir={app.template_folder} exists={Path(app.template_folder).exists()} index={p.exists()}"
    )

@app.errorhandler(Exception)
def handle_any(e):
    app.logger.error("Unhandled error on request:\n%s", traceback.format_exc())
    return "Internal Server Error", 500


@app.get("/health")
def health():
    return "ok", 200

@app.get("/test")
def test():
    return "server ok", 200

# Handle Render’s HEAD probe + your normal GET page
@app.route("/", methods=["GET", "HEAD"])
def home():
    if request.method == "HEAD":
        return "", 200
    return render_template("index.html")

BASE_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)

# strong logging so we see errors in Render logs
logging.basicConfig(level=logging.INFO)

@app.before_first_request
def startup_note():
    p = Path(app.template_folder) / "index.html"
    app.logger.info(f"[startup] templates dir={app.template_folder} exists={Path(app.template_folder).exists()} index={p.exists()}")

# HEAD-safe home that renders your template

@app.route("/", methods=["GET", "HEAD"])
def home():
    if request.method == "HEAD":
        # Render’s automatic health checks use HEAD requests.
        # We respond with 200 OK and no content.
        return "", 200
    return render_template("index.html")

# plain text test route (proves server is fine even if template breaks)
@app.get("/test")
def test():
    return "server ok", 200

# health route for quick probe
@app.get("/health")
def health():
    return "ok", 200

# catch-all to surface exact error in logs
@app.errorhandler(Exception)
def handle_any(e):
    app.logger.error("Unhandled error on request:\n%s", traceback.format_exc())
    return "Internal Server Error", 500

BASE_BANDS = {
    ("lagging/insulation", "pre-1980"): (5.0, 10.0),
    ("maintenance/demolition", "pre-1980"): (0.5, 2.0),
    ("cement/board cutting", "pre-1980"): (1.0, 5.0),
    ("garage/brakes", "pre-1980"): (0.2, 1.0),
    ("bystander", "pre-1980"): (0.1, 0.5),
    ("lagging/insulation", "1980-1999"): (0.5, 2.0),
    ("maintenance/demolition", "1980-1999"): (0.2, 0.8),
    ("bystander", "1980-1999"): (0.05, 0.2),
    ("any", "2000+"): (0.01, 0.05)
}

DISCLAIMER = (
    "Educational use only. This estimator provides a non-diagnostic approximation of cumulative exposure "
    "using literature-style bands and user-entered history. It is not medical or legal advice and does not "
    "determine eligibility for any claim or benefit. Operated in the UK for a UK audience. "
    "© 2025 Dr W. Kent. Independent of sponsors; no editorial input from any funder."
)

def band_for(task, era):
    key = (task.lower().strip(), era.strip())
    if key in BASE_BANDS:
        return BASE_BANDS[key]
    if era == "2000+":
        return BASE_BANDS[("any","2000+")]
    return (0.05, 0.2)

def control_multiplier(rpe_consistent: bool, lev: bool):
    mult = 1.0
    if rpe_consistent:
        mult *= 0.5
    if lev:
        mult *= 0.8
    return mult

def freq_multiplier(days_per_week: float, hours_per_day: float):
    return (days_per_week/5.0) * (hours_per_day/8.0)

def compute_role(role):
    low, high = band_for(role["task"], role["era"])
    f_mult = freq_multiplier(float(role["days_per_week"]), float(role["hours_per_day"]))
    c_mult = control_multiplier(bool(role["rpe"]), bool(role["lev"]))
    adj_low = low * f_mult * c_mult
    adj_high = high * f_mult * c_mult
    years = max(0, int(role["end_year"]) - int(role["start_year"]))
    dose_low = adj_low * years
    dose_high = adj_high * years
    return {
        "task": role["task"],
        "era": role["era"],
        "years": years,
        "base_band": [low, high],
        "adjusted_band": [adj_low, adj_high],
        "dose_range": [dose_low, dose_high]
    }

from flask import render_template

from pathlib import Path
from flask import Flask, render_template, request  # request may be new

@app.route("/")
def index():
    return render_template("index.html", year=datetime.now().year)

@app.route("/estimate", methods=["POST"])
def estimate():
    data = request.get_json(force=True)
    roles = data.get("roles", [])
    summaries = []
    total_low = 0.0
    total_high = 0.0
    first_exposure_year = None
    for r in roles:
        res = compute_role(r)
        summaries.append(res)
        total_low += res["dose_range"][0]
        total_high += res["dose_range"][1]
        sy = int(r.get("start_year"))
        if first_exposure_year is None or sy < first_exposure_year:
            first_exposure_year = sy
    latency = None
    if first_exposure_year:
        latency = datetime.now().year - first_exposure_year

    context = {
        "summaries": summaries,
        "total_range": [round(total_low,1), round(total_high,1)],
        "latency_years": latency,
        "disclaimer": DISCLAIMER
    }
    return jsonify(context)

@app.route("/export_pdf", methods=["POST"])
def export_pdf():
    payload = request.get_json(force=True)
    doc_buf = BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(doc_buf, pagesize=A4)
    elems = []
    elems.append(Paragraph("<b>Asbestos Exposure Educational Estimator — Summary</b>", styles["Title"]))
    elems.append(Spacer(1, 12))
    roles = payload.get("roles", [])
    for i, r in enumerate(roles, start=1):
        elems.append(Paragraph(f"<b>Role {i}:</b> {r['task']} ({r['era']}) {r['start_year']}–{r['end_year']}", styles["BodyText"]))
        elems.append(Paragraph(f"Days/week: {r['days_per_week']}, Hours/day: {r['hours_per_day']}, RPE: {bool(r['rpe'])}, LEV: {bool(r['lev'])}", styles["BodyText"]))
        elems.append(Spacer(1,6))
    elems.append(Spacer(1, 6))
    totals = payload.get("totals", {"low":0,"high":0,"latency":None})
    elems.append(Paragraph(f"<b>Cumulative exposure (f/ml·years):</b> {totals['low']}–{totals['high']}", styles["Heading2"]))
    if totals.get("latency") is not None:
        elems.append(Paragraph(f"<b>Latency (years since first exposure):</b> ~{totals['latency']}", styles["BodyText"]))
    elems.append(Spacer(1, 12))
    interp = [
        ["Educational context (not diagnostic)"],
        ["• Asbestosis/Diffuse pleural thickening often associated with ~10–25+ f/ml·years."],
        ["• Lung cancer without asbestosis: typically very high cumulative exposures."],
        ["• Mesothelioma: no safe threshold; qualitative exposure history remains important."],
    ]
    table = Table(interp, colWidths=[480])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0), colors.lightgrey),
                               ("BOX",(0,0),(-1,-1),0.5,colors.black),
                               ("INNERGRID",(0,0),(-1,-1),0.25,colors.grey)]))
    elems.append(table)
    elems.append(Spacer(1, 12))
    elems.append(Paragraph("<b>Disclaimer</b>", styles["Heading3"]))
    elems.append(Paragraph(payload.get("disclaimer", ""), styles["BodyText"]))
    doc.build(elems)
    doc_buf.seek(0)
    return send_file(doc_buf, mimetype="application/pdf", as_attachment=True, download_name="asbestos_estimate_summary.pdf")

@app.route("/ai/parse_history", methods=["POST"])
def ai_parse_history():
    data = request.get_json(force=True)
    text = (data or {}).get("text","").lower()
    # Naive keyword mapping
    task = "bystander"
    if "lagger" in text or "lagging" in text or "insulation" in text: task = "lagging/insulation"
    elif "demolition" in text or "maintenance" in text: task = "maintenance/demolition"
    elif "cement" in text or "board" in text or "cutting" in text: task = "cement/board cutting"
    elif "garage" in text or "brake" in text: task = "garage/brakes"

    era = "pre-1980" if any(y.startswith("196") or y.startswith("195") for y in text.split()) else \
          "1980-1999" if "198" in text or "199" in text else "2000+"

    rpe = "mask" in text or "respirat" in text
    lev = "ventilation" in text or "lev" in text or "extract" in text

    import re
    years = [int(y) for y in re.findall(r"\b(19[5-9]\d|20[0-2]\d)\b", text)]
    start_year = min(years) if years else 1980
    end_year = max(years) if years else start_year + 5

    result = {"roles":[{
        "task": task, "era": era,
        "start_year": start_year, "end_year": end_year,
        "days_per_week": 5, "hours_per_day": 6,
        "rpe": bool(rpe), "lev": bool(lev)
    }]}
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

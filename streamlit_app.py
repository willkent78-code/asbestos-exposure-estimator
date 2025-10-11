import streamlit as st
from dataclasses import dataclass

st.set_page_config(page_title="Asbestos Exposure Estimator", page_icon="🧪", layout="centered")

@dataclass
class ExposureInput:
    job_title: str
    environment: str
    duration_years: float
    intensity_level: str
    ppe: str

INTENSITY_FACTORS = {"Very low": 0.5, "Low": 1.0, "Moderate": 2.0, "High": 4.0, "Very high": 8.0}
PPE_FACTORS = {"None": 1.0, "Basic mask": 0.7, "Respirator (P2/P3)": 0.4, "Powered respirator": 0.25}

def estimate(e: ExposureInput) -> float:
    base = INTENSITY_FACTORS[e.intensity_level]
    env = 1.3 if e.environment == "Confined/poorly ventilated" else 1.0
    ppe = PPE_FACTORS[e.ppe]
    return e.duration_years * base * env * ppe

def band(score: float) -> str:
    if score < 2: return "Minimal"
    if score < 5: return "Low"
    if score < 10: return "Moderate"
    if score < 20: return "High"
    return "Very high"

st.title("Asbestos Exposure Estimator (Streamlit)")
st.write("**Prototype** for educational use. Not a diagnostic device.")

with st.form("exposure_form"):
    c1, c2 = st.columns(2)
    job = c1.text_input("Job/role", placeholder="e.g., Lagging, Demolition, Shipyard")
    env = c2.selectbox("Environment", ["Well ventilated", "Confined/poorly ventilated"])
    years = c1.number_input("Duration of exposure (years)", min_value=0.0, max_value=60.0, step=0.5, value=1.0)
    intensity = c2.selectbox("Intensity level", list(INTENSITY_FACTORS.keys()))
    ppe = c1.selectbox("PPE used", list(PPE_FACTORS.keys()))
    go = st.form_submit_button("Estimate exposure")

if go:
    e = ExposureInput(job, env, years, intensity, ppe)
    score = estimate(e)
    st.metric("Exposure score (arbitrary units)", f"{score:.2f}")
    st.success(f"Estimated risk band: **{band(score)}**")
    with st.expander("Notes"):
        st.write("- Replace thresholds with validated cut-points.\n- Add references/guidelines here.")

st.caption("© 2025 — Prototype. Educational purposes only.")

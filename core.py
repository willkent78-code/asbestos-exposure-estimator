# core.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from datetime import datetime

# === Your existing constants ===
BASE_BANDS: Dict[Tuple[str, str], Tuple[float, float]] = {
    ("lagging/insulation", "pre-1980"): (5.0, 10.0),
    ("maintenance/demolition", "pre-1980"): (0.5, 2.0),
    ("cement/board cutting", "pre-1980"): (1.0, 5.0),
    ("garage/brakes", "pre-1980"): (0.2, 1.0),
    ("bystander", "pre-1980"): (0.1, 0.5),
    ("lagging/insulation", "1980-1999"): (0.5, 2.0),
    ("maintenance/demolition", "1980-1999"): (0.2, 0.8),
    ("bystander", "1980-1999"): (0.05, 0.2),
    ("any", "2000+"): (0.01, 0.05),
}

DISCLAIMER = (
    "Educational use only. This estimator provides a non-diagnostic approximation of cumulative exposure "
    "using literature-style bands and user-entered history. It is not medical or legal advice and does not "
    "determine eligibility for any claim or benefit. Operated in the UK for a UK audience. "
    "© 2025 Dr W. Kent. Independent of sponsors; no editorial input from any funder."
)

def band_for(task: str, era: str) -> Tuple[float, float]:
    key = (task.lower().strip(), era.strip())
    if key in BASE_BANDS:
        return BASE_BANDS[key]
    if era == "2000+":
        return BASE_BANDS[("any", "2000+")]
    return (0.05, 0.2)

def control_multiplier(rpe_consistent: bool, lev: bool) -> float:
    mult = 1.0
    if rpe_consistent:
        mult *= 0.5
    if lev:
        mult *= 0.8
    return mult

def freq_multiplier(days_per_week: float, hours_per_day: float) -> float:
    return (days_per_week / 5.0) * (hours_per_day / 8.0)

def compute_role(role: Dict[str, Any]) -> Dict[str, Any]:
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
        "base_band_low": round(low, 3),
        "base_band_high": round(high, 3),
        "adj_band_low": round(adj_low, 3),
        "adj_band_high": round(adj_high, 3),
        "dose_low": round(dose_low, 3),
        "dose_high": round(dose_high, 3),
    }

def estimate_all(roles: List[Dict[str, Any]]) -> Dict[str, Any]:
    summaries = []
    total_low = 0.0
    total_high = 0.0
    first_exposure_year = None

    for r in roles:
        res = compute_role(r)
        summaries.append(res)
        total_low += res["dose_low"]
        total_high += res["dose_high"]
        sy = int(r["start_year"])
        if first_exposure_year is None or sy < first_exposure_year:
            first_exposure_year = sy

    latency = None
    if first_exposure_year:
        latency = datetime.now().year - first_exposure_year

    return {
        "summaries": summaries,
        "total_low": round(total_low, 2),
        "total_high": round(total_high, 2),
        "latency_years": latency,
        "disclaimer": DISCLAIMER,
    }

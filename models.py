"""Correlations from section 2.2 of Modelos_Fisicos_Candidatos_PAT.pdf.

h = H_t,BEP / H_p,BEP
q = Q_t,BEP / Q_p,BEP

Supply eta_p and eta_h as fractions (0 < eta <= 1).
The Schmiedl correlation uses hydraulic efficiency (eta_h).
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Optional


@dataclass(frozen=True)
class Prediction:
    method: str
    year: int
    h: Optional[float]
    q: Optional[float]
    ht_m: Optional[float]
    qt_m3h: Optional[float]
    formula: str
    observation: str = ""


FORMULAS = {
    "Stepanoff": "h = 1/ηp ; q = 1/√ηp",
    "Childs": "h = 1/ηp ; q = 1/ηp",
    "Sharma": "h = 1/ηp^1,2 ; q = 1/ηp^0,8",
    "Alatorre-Frenk": "h = 1/(0,85·ηp^5 + 0,385) ; q = (0,85·ηp^5 + 0,385)/(2·ηp^9,5 + 0,205)",
    "Schmiedl": "h = −1,4 + 2,5/ηh ; q = −1,5 + 2,4/ηh²",
}


def _validate_eta(name: str, x: float) -> None:
    if not math.isfinite(x) or not 0 < x <= 1:
        raise ValueError(f"{name} must be greater than 0% and at most 100%.")


def _validate_bep(name: str, value: Optional[float]) -> None:
    if value is not None and (not math.isfinite(value) or value <= 0):
        raise ValueError(f"{name} must be positive and finite.")


def calculate_correlations(
    eta_p: float,
    eta_h: Optional[float] = None,
    qp_bep_m3h: Optional[float] = None,
    hp_bep_m: Optional[float] = None,
) -> list[Prediction]:
    """Calculate the correlations from section 2.2.

    Supply eta_p and eta_h as fractions (e.g., 0.70). When eta_h is None,
    hydraulic efficiency is unknown and the Schmiedl result is unavailable.
    The optional Qp and Hp inputs scale the dimensionless results.
    """
    _validate_eta("ηp", eta_p)
    if eta_h is not None:
        _validate_eta("ηh", eta_h)
    _validate_bep("Qp,BEP", qp_bep_m3h)
    _validate_bep("Hp,BEP", hp_bep_m)

    denom_a = 0.85 * eta_p**5 + 0.385
    rows: list[tuple[str, int, Optional[float], Optional[float], str]] = [
        ("Stepanoff", 1957, 1/eta_p, 1/math.sqrt(eta_p), ""),
        ("Childs", 1962, 1/eta_p, 1/eta_p, ""),
        ("Sharma", 1985, 1/(eta_p**1.2), 1/(eta_p**0.8), ""),
        ("Alatorre-Frenk", 1994, 1/denom_a,
         denom_a/(2*eta_p**9.5 + 0.205), ""),
    ]
    if eta_h is None:
        rows.append(("Schmiedl", 1988, None, None,
                     "Requires ηh (hydraulic efficiency) as a separate input from ηp."))
    else:
        rows.append(("Schmiedl", 1988, -1.4 + 2.5/eta_h,
                     -1.5 + 2.4/(eta_h**2), ""))

    predictions = []
    for name, year, h, q, obs in rows:
        if h is not None and q is not None:
            if not (math.isfinite(h) and math.isfinite(q)):
                raise ValueError("Check the efficiency values you entered. The calculation requires a finite result.")
            if h <= 1 or q <= 1:
                obs = (obs + " Warning: h ≤ 1 or q ≤ 1. Check the range of applicability.").strip()
        predictions.append(Prediction(
            method=name, year=year, h=h, q=q,
            ht_m=None if h is None or hp_bep_m is None else h*hp_bep_m,
            qt_m3h=None if q is None or qp_bep_m3h is None else q*qp_bep_m3h,
            formula=FORMULAS[name], observation=obs,
        ))
    return predictions


def calculate_from_percent(
    eta_p_percent: float,
    eta_h_percent: Optional[float] = None,
    qp_bep_m3h: Optional[float] = None,
    hp_bep_m: Optional[float] = None,
) -> list[Prediction]:
    """Calculate correlations using percentage inputs from the interface (e.g., 70)."""
    return calculate_correlations(
        eta_p=eta_p_percent/100,
        eta_h=None if eta_h_percent is None else eta_h_percent/100,
        qp_bep_m3h=qp_bep_m3h,
        hp_bep_m=hp_bep_m,
    )

"""
Deterministic, location-only hazard scoring — no LLM involved.

Unlike a full underwriting risk score, this only uses hazard exposure at the
address itself (flood, wildfire, seismic, fault proximity, coastal proximity).
It intentionally excludes building-specific factors (construction, occupancy,
year built, sprinklers) since those aren't available from an address alone.
"""

FLOOD_ZONE_SCORES = {
    "VE": 35, "AE": 30, "AO": 25, "AH": 25, "A": 22,
    "X500": 8, "X": 0, "D": 5,
}

_WILDFIRE_POINTS = {0: 0, 1: 3, 2: 8, 3: 14, 4: 20}
_WILDFIRE_LABELS = {1: "Low", 2: "Medium", 3: "High", 4: "Very High"}


def score_location(hazards: dict) -> dict:
    flood_available = hazards.get("flood_available", True)
    flood_zone = hazards.get("flood_zone", "X")
    sfha = hazards.get("sfha", False)
    wildfire = hazards.get("wildfire_score", 0)
    pga = hazards.get("seismic_pga", 0.0)
    fault_mi = hazards.get("fault_distance_miles", 999.0)
    coastal_mi = hazards.get("coastal_distance_miles", 999.0)

    drivers = []
    raw = 0

    # Flood (max 35) — only scored when FEMA lookup actually succeeded;
    # an unavailable lookup is reported as unknown, never assumed zero-risk.
    if not flood_available:
        drivers.append("Flood zone data unavailable (FEMA lookup failed)")
    else:
        flood_score = FLOOD_ZONE_SCORES.get(flood_zone, 0)
        if sfha and flood_score < 22:
            flood_score = 22
        if flood_score > 0:
            raw += flood_score
            drivers.append(f"Flood Zone {flood_zone}")

    # Wildfire (max 20)
    wf_score = _WILDFIRE_POINTS.get(wildfire, 0)
    if wf_score > 0:
        raw += wf_score
        drivers.append(f"Wildfire {_WILDFIRE_LABELS.get(wildfire, 'Low')}")

    # Seismic (max 20)
    if pga >= 0.5:
        raw += 20; drivers.append(f"Seismic PGA {pga}g (very high)")
    elif pga >= 0.3:
        raw += 14; drivers.append(f"Seismic PGA {pga}g (high)")
    elif pga >= 0.2:
        raw += 9; drivers.append(f"Seismic PGA {pga}g (moderate)")
    elif pga >= 0.1:
        raw += 4

    # Fault proximity bonus (max 6)
    if fault_mi < 5:
        raw += 6; drivers.append(f"Active fault {fault_mi} mi away")
    elif fault_mi < 15:
        raw += 3

    # Coastal / wind exposure (max 15)
    if coastal_mi <= 1:
        raw += 15; drivers.append("Immediate coastal exposure")
    elif coastal_mi <= 5:
        raw += 11; drivers.append(f"Coastal proximity {coastal_mi} mi")
    elif coastal_mi <= 10:
        raw += 7; drivers.append(f"Coastal proximity {coastal_mi} mi")
    elif coastal_mi <= 25:
        raw += 3

    raw = max(0, min(100, raw))

    if raw >= 50:
        tier = "Very High"
    elif raw >= 35:
        tier = "High"
    elif raw >= 18:
        tier = "Moderate"
    else:
        tier = "Low"

    return {
        "hazard_score": raw,
        "hazard_tier": tier,
        "hazard_drivers": drivers[:5],
    }

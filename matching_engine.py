"""
Matching engine: scores donor–request pairs using
  1. Blood-type / organ compatibility
  2. Geographic proximity (haversine distance)
  3. Urgency multiplier
"""

import math
from typing import Optional

# ── Blood-type compatibility chart ────────────────────────────────────────────
# Key = recipient blood type  →  Value = list of acceptable donor blood types
BLOOD_COMPATIBILITY: dict[str, list[str]] = {
    "A+":  ["A+", "A-", "O+", "O-"],
    "A-":  ["A-", "O-"],
    "B+":  ["B+", "B-", "O+", "O-"],
    "B-":  ["B-", "O-"],
    "AB+": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    "AB-": ["A-", "B-", "AB-", "O-"],
    "O+":  ["O+", "O-"],
    "O-":  ["O-"],
}

# Organs that can be donated (living or deceased) – kept simple
ORGANS = [
    "Blood",
    "Kidney",
    "Liver",
    "Heart",
    "Lung",
    "Pancreas",
    "Cornea",
    "Bone Marrow",
    "Skin",
    "Small Intestine",
]

URGENCY_WEIGHT = {
    "Critical": 1.5,
    "High":     1.2,
    "Medium":   1.0,
    "Low":      0.8,
}


def is_blood_compatible(donor_bt: str, recipient_bt: str) -> bool:
    """Return True if donor blood type is acceptable for recipient."""
    return donor_bt in BLOOD_COMPATIBILITY.get(recipient_bt, [])


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two (lat, lon) points in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def location_score(dist_km: float, max_km: float = 2000.0) -> float:
    """
    Convert distance to a 0–1 score (1 = same location, 0 = very far).
    Uses an exponential decay so nearby donors rank much higher.
    """
    return math.exp(-dist_km / max_km)


def compute_match_score(
    donor: dict,
    request: dict,
    weight_blood: float = 0.45,
    weight_organ: float = 0.35,
    weight_location: float = 0.20,
) -> Optional[float]:
    """
    Returns a composite score in [0, 1] × urgency multiplier,
    or None if the match is fundamentally incompatible.
    """
    needed = request["needed_organ"]
    donor_organs: list = donor.get("organs", [])

    # ── Organ compatibility ──────────────────────────────────────────────────
    if needed == "Blood":
        # Blood-only donation: organ list doesn't matter, blood type does
        organ_ok = True
    else:
        # For solid organs, donor must have listed the organ AND blood must match
        organ_ok = needed in donor_organs

    if not organ_ok:
        return None

    # ── Blood type compatibility ─────────────────────────────────────────────
    blood_ok = is_blood_compatible(donor["blood_type"], request["blood_type"])
    if not blood_ok:
        return None  # hard disqualifier

    blood_bonus = 1.0 if donor["blood_type"] == request["blood_type"] else 0.7

    # ── Location score ───────────────────────────────────────────────────────
    d_lat, d_lon = donor.get("lat"), donor.get("lon")
    r_lat, r_lon = request.get("lat"), request.get("lon")

    if d_lat and d_lon and r_lat and r_lon:
        dist = haversine_km(d_lat, d_lon, r_lat, r_lon)
        loc_sc = location_score(dist)
    else:
        # Fall back: same city → 0.9, same state → 0.6, else 0.3
        if donor.get("city", "").lower() == request.get("city", "").lower():
            loc_sc = 0.9
        elif donor.get("state", "").lower() == request.get("state", "").lower():
            loc_sc = 0.6
        else:
            loc_sc = 0.3

    # ── Composite score ──────────────────────────────────────────────────────
    organ_score = 1.0  # binary – already filtered incompatible
    raw = (
        weight_blood    * blood_bonus +
        weight_organ    * organ_score +
        weight_location * loc_sc
    )

    urgency_mult = URGENCY_WEIGHT.get(request.get("urgency", "High"), 1.2)
    final = min(raw * urgency_mult, 1.0)
    return round(final, 4)


def find_top_matches(request: dict, donors: list[dict], top_n: int = 10) -> list[dict]:
    """
    Score all available donors against a request and return the top N matches.
    Each result dict includes: donor_id, score, distance_km, blood_match_type.
    """
    results = []

    for donor in donors:
        if not donor.get("available", True):
            continue

        score = compute_match_score(donor, request)
        if score is None:
            continue

        # Distance label
        d_lat, d_lon = donor.get("lat"), donor.get("lon")
        r_lat, r_lon = request.get("lat"), request.get("lon")
        if d_lat and d_lon and r_lat and r_lon:
            dist_km = round(haversine_km(d_lat, d_lon, r_lat, r_lon), 1)
        else:
            dist_km = None

        blood_match = (
            "Exact" if donor["blood_type"] == request["blood_type"] else "Compatible"
        )

        results.append({
            "donor_id":         donor["id"],
            "donor_name":       donor["name"],
            "donor_blood_type": donor["blood_type"],
            "donor_organs":     donor.get("organs", []),
            "donor_city":       donor.get("city", ""),
            "donor_state":      donor.get("state", ""),
            "donor_phone":      donor.get("phone", ""),
            "score":            score,
            "distance_km":      dist_km,
            "blood_match":      blood_match,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]

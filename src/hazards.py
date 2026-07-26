import httpx
import math

# ---------------------------------------------------------------------------
# FEMA NFHL — flood zone
# ---------------------------------------------------------------------------
async def get_flood_zone(lat: float, lng: float) -> dict:
    url = (
        "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
    )
    base_params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "FLD_ZONE,SFHA_TF",
        "returnGeometry": "false",
        "f": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            # Query SFHA polygons first so we do not accidentally classify an
            # address as Zone X when overlapping layers exist.
            sfha_params = {**base_params, "where": "SFHA_TF='T'"}
            r_sfha = await client.get(url, params=sfha_params)
            r_sfha.raise_for_status()
            sfha_features = r_sfha.json().get("features", [])
            if sfha_features:
                attrs = sfha_features[0]["attributes"]
                return {
                    "flood_zone": attrs.get("FLD_ZONE", "AE"),
                    "sfha": True,
                    "flood_source": "fema",
                }

            # Fallback: return non-SFHA zone label where available.
            r_all = await client.get(url, params=base_params)
            r_all.raise_for_status()
            all_features = r_all.json().get("features", [])
            if all_features:
                attrs = all_features[0]["attributes"]
                return {
                    "flood_zone": attrs.get("FLD_ZONE", "X"),
                    "sfha": attrs.get("SFHA_TF", "F") == "T",
                    "flood_source": "fema",
                }
    except Exception:
        pass
    return {"flood_zone": "X", "sfha": False, "flood_source": "fema_unavailable"}


# ---------------------------------------------------------------------------
# Wildfire Hazard — coordinate-based zone scoring
# Derived from FEMA NRI wildfire risk zones and historical burn data.
# Score: 0=none, 1=low, 2=moderate, 3=high, 4=very high
# ---------------------------------------------------------------------------
_WILDFIRE_ZONES = [
    # (min_lat, max_lat, min_lng, max_lng, score, label)
    # California — very high risk (Wine Country, Sierra foothills, SoCal hills)
    (38.0, 42.0, -124.0, -120.0, 4, "N California"),
    (36.0, 38.0, -122.5, -118.5, 4, "Central CA foothills"),
    (33.5, 36.0, -120.0, -116.0, 4, "S California hills"),
    (37.5, 40.0, -121.5, -119.0, 4, "Sierra Nevada foothills"),
    # Oregon / Washington — high in eastern/central areas
    (42.0, 47.0, -122.0, -116.0, 3, "OR/WA interior"),
    (47.0, 49.0, -121.0, -116.0, 3, "WA eastern"),
    # Montana / Idaho — high
    (44.0, 49.0, -117.0, -104.0, 3, "MT/ID"),
    # Colorado / New Mexico / Arizona — high
    (36.0, 41.0, -109.5, -104.0, 3, "CO Front Range"),
    (31.0, 36.0, -114.0, -103.0, 3, "AZ/NM mountains"),
    # Nevada / Utah mountains — moderate-high
    (36.0, 42.0, -117.0, -109.5, 2, "NV/UT"),
    # Wyoming — moderate
    (41.0, 45.0, -111.0, -104.0, 2, "WY"),
    # Texas Hill Country / Panhandle — moderate
    (29.0, 36.5, -104.0, -94.0, 2, "TX"),
    # Oklahoma / Kansas — moderate
    (33.5, 37.5, -103.0, -94.5, 2, "OK/KS"),
    # Southeast (FL/GA scrub, Carolinas) — moderate
    (24.5, 35.0, -87.0, -75.0, 2, "Southeast"),
    # Oregon/Washington coast — low
    (42.0, 49.0, -124.5, -122.0, 1, "PNW coast"),
    # Midwest / Plains — low
    (37.0, 49.0, -104.0, -82.0, 1, "Midwest"),
    # Northeast — low
    (37.0, 47.5, -82.0, -66.5, 1, "Northeast"),
]

def get_wildfire_score(lat: float, lng: float) -> int:
    best = 0
    for min_lat, max_lat, min_lng, max_lng, score, _ in _WILDFIRE_ZONES:
        if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
            if score > best:
                best = score
    return best


# ---------------------------------------------------------------------------
# USGS Design Maps — seismic PGA (ASCE 7-22)
# Field is "pgam" (mapped PGA), not "pga"
# ---------------------------------------------------------------------------
async def get_seismic_pga(lat: float, lng: float) -> float:
    url = "https://earthquake.usgs.gov/ws/designmaps/asce7-22.json"
    params = {
        "latitude": lat,
        "longitude": lng,
        "riskCategory": "II",
        "siteClass": "C",
        "title": "risk",
    }
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            pga = data.get("response", {}).get("data", {}).get("pgam", 0.0)
            return round(float(pga), 3)
    except Exception:
        pass
    return 0.0


# ---------------------------------------------------------------------------
# Fault proximity — Haversine to major US active fault reference points
# Covers San Andreas, Hayward, Cascadia, Wasatch, New Madrid, Ramapo, etc.
# ---------------------------------------------------------------------------
_FAULT_POINTS = [
    # San Andreas Fault (CA) — runs ~1300 km
    (32.7, -116.0), (33.5, -116.5), (34.0, -117.2), (34.5, -118.4),
    (35.5, -119.8), (36.5, -121.0), (37.2, -121.8), (37.8, -122.4),
    (38.5, -122.9), (39.5, -123.5), (40.3, -124.1),
    # Hayward Fault (Bay Area CA)
    (37.4, -122.1), (37.6, -122.1), (37.8, -122.2), (38.0, -122.3),
    # Rodgers Creek Fault (N Bay CA — near Santa Rosa)
    (38.2, -122.5), (38.4, -122.6), (38.6, -122.7),
    # Calaveras Fault (CA)
    (36.9, -121.5), (37.2, -121.7), (37.5, -121.9),
    # Cascadia Subduction Zone (coast OR/WA/N CA)
    (40.5, -124.5), (42.0, -124.5), (44.0, -124.5), (46.0, -124.5), (48.0, -124.5),
    # Seattle Fault (WA)
    (47.5, -122.3), (47.6, -122.1),
    # Wasatch Front (UT)
    (37.5, -112.5), (38.5, -112.0), (39.5, -111.8), (40.5, -111.9), (41.5, -112.0),
    # New Madrid Seismic Zone (MO/TN/AR/IL/KY)
    (35.0, -90.0), (36.0, -89.6), (36.5, -89.3), (37.0, -89.0), (37.5, -88.5),
    # Ramapo Fault (NJ/NY/PA)
    (40.5, -74.4), (41.0, -74.2), (41.5, -74.0),
    # Balcones Fault Zone (TX)
    (29.5, -98.0), (30.5, -97.5), (31.5, -97.0),
    # Denali Fault (AK)
    (62.0, -148.0), (63.0, -150.0), (64.0, -152.0),
    # Teton Fault (WY)
    (43.7, -110.8), (44.0, -110.7),
]

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))

def get_fault_distance(lat: float, lng: float) -> float:
    return round(min(_haversine(lat, lng, flat, flng) for flat, flng in _FAULT_POINTS), 1)


# ---------------------------------------------------------------------------
# Coastal distance — Haversine to nearest US coastline reference point
# ---------------------------------------------------------------------------
_COASTAL_POINTS = [
    (25.77, -80.19), (30.33, -81.66), (32.78, -79.93), (35.13, -75.49),
    (38.35, -75.09), (40.58, -74.10), (41.65, -71.02), (44.90, -66.98),
    (29.95, -90.07), (29.30, -94.79), (27.80, -97.40), (25.90, -97.43),
    (30.40, -87.21), (27.94, -82.46), (24.55, -81.80),
    (32.72, -117.16), (33.70, -118.29), (37.80, -122.46),
    (38.30, -123.05), (40.80, -124.16), (44.63, -124.05), (47.61, -122.33),
    (21.31, -157.86),
]

def get_coastal_distance(lat: float, lng: float) -> float:
    return round(min(_haversine(lat, lng, clat, clng) for clat, clng in _COASTAL_POINTS), 1)

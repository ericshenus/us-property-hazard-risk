import asyncio

from geocode import geocode_address
from hazards import (
    get_flood_zone,
    get_wildfire_score,
    get_seismic_pga,
    get_fault_distance,
    get_coastal_distance,
)
from scoring import score_location


async def assess_address(address: str) -> dict:
    geo = await geocode_address(address)
    if not geo:
        return {
            "input_address": address,
            "validated": False,
            "message": (
                "Address could not be validated against the US Census Bureau "
                "geocoder. Check spelling and confirm it is a US postal address "
                "(this tool only covers the US)."
            ),
        }

    lat, lng = geo["lat"], geo["lng"]

    flood, pga = await asyncio.gather(
        get_flood_zone(lat, lng),
        get_seismic_pga(lat, lng),
    )
    wildfire = get_wildfire_score(lat, lng)
    fault_dist = get_fault_distance(lat, lng)
    coastal_dist = get_coastal_distance(lat, lng)

    flood_available = flood.get("flood_source") != "fema_unavailable"
    hazards = {
        "flood_zone": flood["flood_zone"] if flood_available else None,
        "sfha": flood["sfha"] if flood_available else None,
        "flood_available": flood_available,
        "wildfire_score": wildfire,
        "seismic_pga": pga,
        "fault_distance_miles": fault_dist,
        "coastal_distance_miles": coastal_dist,
    }
    scores = score_location(hazards)

    return {
        "input_address": address,
        "matched_address": geo["matched_address"],
        "validated": True,
        "lat": lat,
        "lng": lng,
        **hazards,
        **scores,
    }

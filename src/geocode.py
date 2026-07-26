import httpx

CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"


async def geocode_address(address: str) -> dict | None:
    """Geocode and validate a single US address via the free US Census Bureau geocoder.

    Returns None if the address has no match (i.e. failed validation).
    """
    params = {
        "address": address,
        "benchmark": "Public_AR_Current",
        "format": "json",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(CENSUS_URL, params=params)
        r.raise_for_status()
        data = r.json()

    matches = data.get("result", {}).get("addressMatches", [])
    if not matches:
        return None

    match = matches[0]
    coords = match["coordinates"]
    return {
        "matched_address": match.get("matchedAddress", address),
        "lat": coords["y"],
        "lng": coords["x"],
    }

from pydantic import BaseModel, Field


class HazardAssessment(BaseModel):
    """Hazard exposure result for a single US property address."""

    input_address: str = Field(description="The address as provided by the caller")
    validated: bool = Field(description="Whether the address was successfully validated/geocoded")
    message: str | None = Field(None, description="Explanation of why validation failed, if it did")
    matched_address: str | None = Field(None, description="Normalized address returned by the geocoder")
    lat: float | None = Field(None, description="Latitude of the matched address")
    lng: float | None = Field(None, description="Longitude of the matched address")
    flood_zone: str | None = Field(None, description="FEMA flood zone code (e.g. AE, X, VE); null if unavailable")
    sfha: bool | None = Field(None, description="Whether the address is in a Special Flood Hazard Area")
    flood_available: bool | None = Field(None, description="Whether the FEMA flood zone lookup succeeded")
    wildfire_score: int | None = Field(None, description="Coarse wildfire hazard tier, 0 (none) to 4 (very high)")
    seismic_pga: float | None = Field(None, description="USGS peak ground acceleration in g (ASCE 7-22)")
    fault_distance_miles: float | None = Field(None, description="Distance to the nearest known active fault, in miles")
    coastal_distance_miles: float | None = Field(None, description="Distance to the nearest coastline, in miles")
    hazard_score: int | None = Field(None, description="Deterministic location-only hazard score, 0-100")
    hazard_tier: str | None = Field(None, description="Hazard tier label: Low, Moderate, High, or Very High")
    hazard_drivers: list[str] | None = Field(None, description="Up to 5 human-readable factors driving the score")

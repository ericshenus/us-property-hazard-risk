import os

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from models import HazardAssessment
from risk import assess_address

mcp = FastMCP(
    "Property Hazard MCP",
    instructions=(
        "Looks up flood, wildfire, earthquake, and coastal-storm hazard exposure "
        "for a single US property address, using only free public data sources "
        "(US Census Bureau geocoder, FEMA NFHL, USGS). US addresses only."
    ),
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=int(os.getenv("MCP_PORT", "8000")),
    stateless_http=True,
)


@mcp.tool(
    title="Assess Property Hazard Risk",
    annotations=ToolAnnotations(
        title="Assess Property Hazard Risk",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
    structured_output=True,
)
async def assess_property_hazard(address: str) -> HazardAssessment:
    """Assess natural hazard exposure for a single US property address.

    Validates and geocodes the address (US Census Bureau geocoder), then looks
    up FEMA flood zone, wildfire hazard, USGS seismic PGA, active fault
    proximity, and coastal proximity. Returns a location-only hazard score
    (0-100) and tier. US addresses only; no building characteristics required.
    """
    result = await assess_address(address)
    return HazardAssessment(**result)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

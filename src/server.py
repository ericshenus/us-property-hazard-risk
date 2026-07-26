import os

from mcp.server.fastmcp import FastMCP

from risk import assess_address

mcp = FastMCP(
    "us-property-hazard-risk",
    instructions=(
        "Looks up flood, wildfire, earthquake, and coastal-storm hazard exposure "
        "for a single US property address, using only free public data sources "
        "(US Census Bureau geocoder, FEMA NFHL, USGS). US addresses only."
    ),
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=int(os.getenv("MCP_PORT", "8000")),
    stateless_http=True,
)


@mcp.tool()
async def assess_property_hazard(address: str) -> dict:
    """Assess natural hazard exposure for a single US property address.

    Validates and geocodes the address (US Census Bureau geocoder), then looks
    up FEMA flood zone, wildfire hazard, USGS seismic PGA, active fault
    proximity, and coastal proximity. Returns a location-only hazard score
    (0-100) and tier. US addresses only; no building characteristics required.
    """
    return await assess_address(address)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

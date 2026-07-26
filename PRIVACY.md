# Privacy Policy

**Property Hazard MCP** (`us-property-hazard-risk`) is a free, keyless MCP server that looks up
natural hazard exposure for a US property address. This policy explains what happens to
data you send it.

## What data we process

- **Address input**: When you call `assess_property_hazard`, the address you provide is sent
  server-side to three free, public government data sources to produce the result:
  - [US Census Bureau Geocoder](https://geocoding.geo.census.gov)
  - [FEMA National Flood Hazard Layer](https://hazards.fema.gov)
  - [USGS Design Maps](https://earthquake.usgs.gov)

  Each of these is a third-party government service with its own data handling practices; we
  don't control their logging or retention.

## What we don't do

- No accounts, no authentication, no API keys — there's nothing tied to an identity to begin with.
- No database. The address and the resulting hazard data are not stored; each request is
  processed and returned without persistence.
- No cookies, no analytics, no tracking, no advertising.
- We do not sell or share data for marketing purposes.

## Access logs

Like any web server, routine infrastructure logs (timestamp, requesting IP, request path) are
kept briefly for operational troubleshooting and abuse prevention, then rotated out (capped at a
few log files of a few megabytes each). These logs are not used for anything beyond that.

## Changes

If this policy changes, the update will be reflected in this file's Git history in the
[public repository](https://github.com/ericshenus/us-property-hazard-risk).

## Contact

Questions or concerns: [info@zipquote.ai](mailto:info@zipquote.ai)

# us-property-hazard-risk (MCP server)

A remote [MCP](https://modelcontextprotocol.io) server that assesses natural
hazard exposure — flood, wildfire, earthquake, and coastal proximity — for a
single US property address, using only free, keyless public data. No API
keys, no database, no map. Works from Claude, ChatGPT, or any other
MCP-compatible host.

## Tool

### `assess_property_hazard(address: str)`

Validates and geocodes the address, then returns flood zone (FEMA NFHL),
wildfire hazard score, seismic PGA (USGS, ASCE 7-22), fault and coastal
distance, and a deterministic 0–100 `hazard_score` / `hazard_tier` with up to
5 `hazard_drivers`. If a data source is unavailable, that field is reported
as unknown rather than assumed zero-risk.

## Data sources

- [US Census Bureau Geocoder](https://geocoding.geo.census.gov) — address validation + geocoding
- [FEMA NFHL](https://hazards.fema.gov) — flood zone
- [USGS Design Maps](https://earthquake.usgs.gov) — seismic PGA
- Static reference points (haversine) — fault + coastal proximity

## Local dev

```bash
python -m venv venv
venv/Scripts/pip install -r requirements.txt   # venv/bin/pip on macOS/Linux

cd src
../venv/Scripts/python server.py               # ../venv/bin/python on macOS/Linux
```

Starts a streamable-HTTP MCP server on `http://localhost:8000/mcp`:

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"assess_property_hazard","arguments":{"address":"1600 Pennsylvania Ave NW, Washington, DC 20500"}}}'
```

## Deployment

Runs via Docker Compose (`docker-compose.yml`):

```bash
docker compose up -d --build
```

## Known limitations

- US addresses only
- FEMA NFHL is occasionally unreachable from some networks (`flood_available: false`)
- Wildfire scoring is a coarse coordinate-zone heuristic, not parcel-level

## License

MIT — see `LICENSE`.

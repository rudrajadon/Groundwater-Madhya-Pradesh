"""
Parse Indore groundwater DB coordinates from DMS-string format into decimal
degrees, and validate against the Indore district bounding box.

The well-master table stores lat/long as strings like:
    46N13225915754300   (this is actually TWO fields concatenated in the
    raw string dump: Latitude "22 25 91" (DD MM SS) and Longitude
    "75 43 00" (DD MM SS), prefixed by toposheet code "46N13")
Real Access exports (via mdb-tools) will give these as two separate columns
(Latitude, Longitude) already split — this parser targets the two-field
case you'll actually get from `mdb-export`. Format observed:
    Latitude:  "22-25-91"  or  "22 25 91"  or  "22°25'91\""  (DD-MM-SS)
    Longitude: "75-43-00"  or similar
Adjust DMS_RE if your exported CSV shows a different separator — check a
few rows after running export_mdb.sh before trusting this at scale.
"""
import re
from dataclasses import dataclass

# Indore district approximate bounding box (sanity-check only, not exact
# administrative boundary) — used to flag likely bad parses for manual review.
INDORE_BBOX = {"lat_min": 22.35, "lat_max": 23.10, "lon_min": 75.35, "lon_max": 76.15}

DMS_RE = re.compile(r"(\d{1,3})[°\-\s](\d{1,2})['\-\s](\d{1,2})")
# Packed 6-digit DMS format: DDMMSS (e.g. "224900" = 22°49'00")
PACKED_DMS_RE = re.compile(r"^(\d{2})(\d{2})(\d{2})$")


@dataclass
class ParsedCoord:
    lat: float | None
    lon: float | None
    valid: bool
    reason: str


def dms_to_decimal(deg: str, minute: str, second: str) -> float:
    d, m, s = float(deg), float(minute), float(second)
    return round(d + m / 60.0 + s / 3600.0, 6)


def parse_dms_string(raw: str) -> float | None:
    if not raw:
        return None
    raw = raw.strip().strip('"').strip("'")
    # Try separated format first (22-49-00, 22°49'00")
    m = DMS_RE.search(raw)
    if m:
        return dms_to_decimal(*m.groups())
    # Try packed 6-digit format (224900)
    m = PACKED_DMS_RE.match(raw)
    if m:
        return dms_to_decimal(*m.groups())
    return None


def parse_and_validate(lat_raw: str, lon_raw: str) -> ParsedCoord:
    lat = parse_dms_string(lat_raw)
    lon = parse_dms_string(lon_raw)
    if lat is None or lon is None:
        return ParsedCoord(lat, lon, False, "unparseable")
    # NOTE: some source strings had a "seconds" field > 59 (e.g. "22-25-91")
    # — almost certainly a data-entry artifact upstream in the mdb, not a
    # bug in this parser. Flag for manual review rather than silently trust.
    lat_stripped = lat_raw.strip().strip('"').strip("'")
    lon_stripped = lon_raw.strip().strip('"').strip("'")
    m_lat = DMS_RE.search(lat_stripped) or PACKED_DMS_RE.match(lat_stripped)
    m_lon = DMS_RE.search(lon_stripped) or PACKED_DMS_RE.match(lon_stripped)
    if m_lat and (int(m_lat.group(2)) >= 60 or int(m_lat.group(3)) >= 60):
        return ParsedCoord(lat, lon, False, "suspect_lat_dms_field")
    if m_lon and (int(m_lon.group(2)) >= 60 or int(m_lon.group(3)) >= 60):
        return ParsedCoord(lat, lon, False, "suspect_lon_dms_field")
    in_box = (
        INDORE_BBOX["lat_min"] <= lat <= INDORE_BBOX["lat_max"]
        and INDORE_BBOX["lon_min"] <= lon <= INDORE_BBOX["lon_max"]
    )
    if not in_box:
        return ParsedCoord(lat, lon, False, "outside_indore_bbox")
    return ParsedCoord(lat, lon, True, "ok")


if __name__ == "__main__":
    # Smoke test against DMS strings in the same shape as those actually
    # observed in IndorePZ.mdb's raw record dump.
    samples = [
        ("22-25-91", "75-43-00"),   # seconds >= 60 -> flagged as suspect_lat_dms_field
        ("22 25 91", "75 43 00"),   # alt separator, also suspect seconds -> suspect_lat_dms_field
        ("00-00-00", "00-00-00"),   # bad data -> outside bbox
        ("", ""),                    # missing -> unparseable
    ]
    for lat_raw, lon_raw in samples:
        result = parse_and_validate(lat_raw, lon_raw)
        print(f"{lat_raw!r:12} {lon_raw!r:12} -> {result}")

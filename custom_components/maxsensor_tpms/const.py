"""Konstanten für MaxSensor TPMS."""
import re

DOMAIN = "maxsensor_tpms"

CONF_AUTO_ADD = "auto_add"
CONF_MIN_RSSI = "min_rssi"
CONF_MANUAL_IDS = "manual_ids"
CONF_IGNORED_IDS = "ignored_ids"

SENSOR_ID_RE = re.compile(r"^[01][0-9A-F]{4}$")


def parse_ids(text: str | None) -> set[str]:
    """Zerlegt eine Liste wie "01A2B, 0BEEF" in gültige Sensor-IDs."""
    if not text:
        return set()
    return {p for p in re.split(r"[,;\s]+", text.upper()) if SENSOR_ID_RE.match(p)}

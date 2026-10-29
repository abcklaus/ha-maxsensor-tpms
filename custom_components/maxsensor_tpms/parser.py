"""Parser für Sysgration/„Multi Wheel BLE TPMS“-Sensoren (reine Python-Datei, ohne HA-Abhängigkeit).

Die Sensoren senden iBeacon-Advertisements (Apple-Hersteller-ID 0x004C). Die Messwerte stecken in
Major/Minor. Das Format wurde aus der Android-App ``com.sysgration.tpms.app`` (v2.8.4) abgeleitet,
siehe docs/PROTOCOL.md.
"""
from __future__ import annotations

from dataclasses import dataclass

APPLE_COMPANY_ID = 0x004C

# iBeacon-UUID -> Sensor-Typ
UUID_TYPE_1 = bytes.fromhex("b54adc0067f911d996690800200c9a66")
UUID_TYPE_2 = bytes.fromhex("b54adc0067f911d996690800200c9a67")
UUID_TYPE_3 = bytes.fromhex("b54adc0067f911d996690800200c9a6a")
UUID_TO_TYPE: dict[bytes, int] = {UUID_TYPE_1: 1, UUID_TYPE_2: 2, UUID_TYPE_3: 3}

PRESSURE_STEP_KPA = 2.5


@dataclass(frozen=True)
class TPMSReading:
    """Ein dekodiertes Advertisement."""

    sensor_id: str
    sensor_type: int
    pressure_kpa: float
    temperature_c: float | None  # None, wenn der Sensor "Batterie schwach" meldet (keine Temperatur)
    battery_low: bool


def parse_manufacturer_data(data: bytes | bytearray) -> TPMSReading | None:
    """Dekodiert die Herstellerdaten (ohne Company-ID) eines iBeacon-Advertisements.

    Gibt ``None`` zurück, wenn es kein Sysgration-TPMS-Advertisement ist.
    """
    if len(data) < 22 or data[0] != 0x02 or data[1] != 0x15:
        return None
    sensor_type = UUID_TO_TYPE.get(bytes(data[2:18]))
    if sensor_type is None:
        return None

    major = int.from_bytes(data[18:20], "big")
    minor_hi = data[20]
    minor_lo = data[21]

    # Sensor-ID wie in der App: Bit 7 des Minor-High-Bytes + Major als 4-stelliges Hex
    sensor_id = f"{minor_hi >> 7}{major:04X}"

    battery_low = False
    temperature: float | None

    if sensor_type == 1:
        raw = minor_hi & 0x7F
        pressure = minor_lo * PRESSURE_STEP_KPA
        if raw == 127:
            battery_low, temperature = True, None
        else:
            temperature = float(raw - 40)
    else:
        raw = minor_hi & 0x3F
        pressure_raw = minor_lo | (0x100 if minor_hi & 0x40 else 0)
        pressure = pressure_raw * PRESSURE_STEP_KPA
        factor = 2 if sensor_type == 2 else 3
        if raw == 63:
            battery_low, temperature = True, None
        else:
            temperature = float(raw * factor - 40)

    return TPMSReading(sensor_id, sensor_type, pressure, temperature, battery_low)


def parse_manufacturer_data_dict(manufacturer_data: dict[int, bytes]) -> TPMSReading | None:
    """Wie ``parse_manufacturer_data``, nimmt aber das Dict ``{company_id: bytes}`` von HA/bleak."""
    data = manufacturer_data.get(APPLE_COMPANY_ID)
    if data is None:
        return None
    return parse_manufacturer_data(data)

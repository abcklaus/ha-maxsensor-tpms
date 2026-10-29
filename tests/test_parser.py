"""Tests für den Parser. Starten mit: python3 -m pytest tests  (oder python3 tests/test_parser.py)."""
import importlib.util
import pathlib
import sys

_p = pathlib.Path(__file__).parents[1] / "custom_components" / "maxsensor_tpms" / "parser.py"
_spec = importlib.util.spec_from_file_location("tpms_parser", _p)
parser = importlib.util.module_from_spec(_spec)
sys.modules["tpms_parser"] = parser
_spec.loader.exec_module(parser)


def frame(uuid: bytes, major: int, minor_hi: int, minor_lo: int) -> bytes:
    return b"\x02\x15" + uuid + major.to_bytes(2, "big") + bytes([minor_hi, minor_lo]) + b"\xc5"


def test_type1_normal():
    # Temp 25 °C -> raw 65, Druck 230 kPa -> 92 Schritte, ID-Bit7 = 1
    r = parser.parse_manufacturer_data(frame(parser.UUID_TYPE_1, 0x1A2B, 0x80 | 65, 92))
    assert r.sensor_id == "11A2B"
    assert r.sensor_type == 1
    assert r.temperature_c == 25.0
    assert r.pressure_kpa == 230.0
    assert not r.battery_low


def test_type1_battery_low():
    r = parser.parse_manufacturer_data(frame(parser.UUID_TYPE_1, 0x0001, 127, 100))
    assert r.sensor_id == "00001"
    assert r.battery_low and r.temperature_c is None
    assert r.pressure_kpa == 250.0


def test_type2_with_pressure_msb():
    # raw temp 30 -> 2*30-40 = 20 °C; Bit6 gesetzt -> Druck (256+10)*2.5 = 665 kPa
    r = parser.parse_manufacturer_data(frame(parser.UUID_TYPE_2, 0xBEEF, 0x40 | 30, 10))
    assert r.sensor_id == "0BEEF"
    assert r.temperature_c == 20.0
    assert r.pressure_kpa == 665.0


def test_type3_and_battery():
    r = parser.parse_manufacturer_data(frame(parser.UUID_TYPE_3, 0x0100, 20, 120))
    assert r.temperature_c == 20 * 3 - 40
    assert r.pressure_kpa == 300.0
    r = parser.parse_manufacturer_data(frame(parser.UUID_TYPE_3, 0x0100, 63, 120))
    assert r.battery_low and r.temperature_c is None


def test_rejects_foreign():
    assert parser.parse_manufacturer_data(b"\x02\x15" + b"\x00" * 20) is None
    assert parser.parse_manufacturer_data(b"\x10\x05\x01") is None
    assert parser.parse_manufacturer_data_dict({0x0006: b"abc"}) is None


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)

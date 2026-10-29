#!/usr/bin/env python3
"""Mitschnitt der TPMS-Advertisements direkt vom Mac/PC (unabhängig von Home Assistant).

Installation:  pip3 install bleak
Start:         python3 tools/ble_sniff.py [Sekunden]   (Standard: 120)
Ausgabe:       Konsole + tools/mitschnitt.csv  (Rohdaten + dekodierte Werte)
"""
import asyncio
import csv
import importlib.util
import pathlib
import sys
import time

from bleak import BleakScanner

root = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("tpms_parser", root / "custom_components/maxsensor_tpms/parser.py")
parser = importlib.util.module_from_spec(spec)
sys.modules["tpms_parser"] = parser
spec.loader.exec_module(parser)

duration = int(sys.argv[1]) if len(sys.argv) > 1 else 120
out = root / "tools" / "mitschnitt.csv"
f = open(out, "w", newline="")
w = csv.writer(f)
w.writerow(["zeit", "adresse", "rssi", "roh_hex", "sensor_id", "typ", "druck_kpa", "druck_bar", "temp_c", "batterie_schwach"])


def on_adv(device, adv):
    data = adv.manufacturer_data.get(0x004C)
    if not data:
        return
    r = parser.parse_manufacturer_data(data)
    if r is None:
        return
    row = [time.strftime("%H:%M:%S"), device.address, adv.rssi, data.hex(), r.sensor_id, r.sensor_type,
           r.pressure_kpa, round(r.pressure_kpa / 100, 2), r.temperature_c, r.battery_low]
    w.writerow(row)
    f.flush()
    print(f"{row[0]}  ID {r.sensor_id}  Typ {r.sensor_type}  {r.pressure_kpa / 100:.2f} bar  "
          f"{r.temperature_c} °C  Batterie schwach={r.battery_low}  RSSI {adv.rssi}  roh={data.hex()}")


async def main():
    print(f"Lausche {duration} s auf TPMS-Sensoren … (Strg+C beendet)")
    async with BleakScanner(on_adv):
        await asyncio.sleep(duration)


asyncio.run(main())

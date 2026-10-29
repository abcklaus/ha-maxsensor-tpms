# Protokoll der Sysgration „Multi Wheel BLE TPMS“-Sensoren

Abgeleitet aus der Android-App `com.sysgration.tpms.app` v2.8.4 (Klassen `ServiceScan`, `e2`).
**Stand: aus dem Code abgeleitet, noch nicht gegen echte Sensoren verifiziert** – siehe `docs/MITSCHNITT_ANLEITUNG.md`.

## Übertragungsart
Die Sensoren senden **iBeacon-Advertisements** (nicht verbindbar, keine GATT-Verbindung). Die App nutzt dafür die
AltBeacon-Bibliothek mit dem Layout `m:2-3=0215,i:4-19,i:20-21,i:22-23,p:24-24` – also ein Standard-iBeacon:

| Offset (Hersteller-Daten, Company-ID 0x004C) | Länge | Inhalt |
|---|---|---|
| 0–1 | 2 | `02 15` (iBeacon) |
| 2–17 | 16 | UUID (bestimmt den Sensor-Typ) |
| 18–19 | 2 | Major (big endian) |
| 20–21 | 2 | Minor (big endian): `minor_hi`, `minor_lo` |
| 22 | 1 | TX-Power (wird nicht ausgewertet) |

## UUID → Typ
| UUID | Typ | Temperatur | Druck |
|---|---|---|---|
| `b54adc00-67f9-11d9-9669-0800200c9a66` | 1 | `(minor_hi & 0x7F) − 40` °C | `minor_lo × 2,5` kPa |
| `b54adc00-67f9-11d9-9669-0800200c9a67` | 2 | `(minor_hi & 0x3F) × 2 − 40` °C | `((minor_hi & 0x40) << 2 \| minor_lo) × 2,5` kPa |
| `b54adc00-67f9-11d9-9669-0800200c9a6a` | 3 | `(minor_hi & 0x3F) × 3 − 40` °C | wie Typ 2 |

## Sensor-ID
`ID = str(minor_hi >> 7) + major als 4-stelliges Hex (Großbuchstaben)`, z. B. `01A2B`. Das ist die ID, die die App anzeigt/abfragt.

## Batterie
Typ 1: `minor_hi & 0x7F == 127` · Typ 2/3: `minor_hi & 0x3F == 63` bedeutet **Batterie schwach**; dann enthält das Advertisement
keine gültige Temperatur (die App zeigt den letzten bekannten Wert). Die Integration verhält sich genauso.

## Einheiten und Sonderwerte
Basiseinheiten sind kPa und °C (die App rechnet für die Anzeige in psi/bar/°F um). Die App begrenzt Temperaturen auf 86 (Typ 1),
84 (Typ 2) bzw. 146 °C (Typ 3); diese Werte entsprechen dem höchsten regulären Rohwert und werden hier unverändert ausgegeben.
Die App löst einen „schnellen Druckverlust“-Alarm aus, wenn der temperaturkompensierte Druck innerhalb von 5 Minuten um > 30 kPa fällt.

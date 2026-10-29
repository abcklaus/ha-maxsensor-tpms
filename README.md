# MaxSensor TPMS für Home Assistant

Home-Assistant-Integration für Reifendrucksensoren der Marke Sysgration (Android-App **„Multi Wheel BLE TPMS“**, Paket
`com.sysgration.tpms.app`) mit im Reifen verbauten Sensoren. Der Empfang läuft über jeden Bluetooth-Adapter von Home Assistant,
**auch über ESPHome-Bluetooth-Proxys (ESP32)**.

> ⚠️ Version 0.1: Das Datenformat wurde aus der App abgeleitet und muss noch mit echten Sensoren abgeglichen werden –
> siehe [docs/MITSCHNITT_ANLEITUNG.md](docs/MITSCHNITT_ANLEITUNG.md).

## Funktionen (pro Rad ein Gerät)
- Reifendruck (intern kPa, Anzeige standardmäßig in bar, in HA frei umstellbar auf psi usw.)
- Temperatur (°C)
- Batterie schwach (Binärsensor)
- Diagnose: Zuletzt gesehen, Signalstärke (RSSI, standardmäßig deaktiviert)
- Letzte Werte bleiben nach Neustarts und zwischen den Fahrten erhalten (die Sensoren senden nur während der Fahrt)

## Installation
1. HACS → ⋮ → *Benutzerdefinierte Repositories* → URL dieses Repos, Kategorie *Integration* → installieren.
   (Manuell: Ordner `custom_components/maxsensor_tpms` nach `config/custom_components/` kopieren.)
2. Home Assistant neu starten.
3. *Einstellungen → Geräte & Dienste → Integration hinzufügen → MaxSensor TPMS* (einmalig bestätigen).

## Automatisches Hinzufügen
Die Integration lauscht **dauerhaft** auf Sensoren (alle drei bekannten Beacon-UUIDs). Sobald ein Sensor zum ersten Mal sendet
(z. B. bei der nächsten Fahrt in Reichweite des Proxys), wird er **ohne Rückfrage** als Gerät „Reifen <ID>“ mit allen Entitäten angelegt.
Der Anlernmodus ist nicht nötig. Danach kannst du das Gerät umbenennen (z. B. „Reifen vorne links“).

Einstellungen (Integration → Konfigurieren):
- **Neue Sensoren automatisch hinzufügen** – ausschalten, wenn nur manuell angelegt werden soll.
- **Mindest-Signalstärke** (z. B. `-80` dBm) – verhindert, dass Fahrzeuge in der Nachbarschaft miterfasst werden.
- **Sensor-IDs manuell vorab anlegen** – die 4 IDs aus der App eintragen: Die Geräte erscheinen sofort, die Werte folgen bei der ersten Übertragung.
- **Ignorierte Sensor-IDs** – werden nie hinzugefügt. Löschst du ein Gerät, landet seine ID automatisch hier.

## ESP32-Bluetooth-Proxy
Die Sensoren senden nicht verbindbare iBeacon-Advertisements. Ein ESPHome-Proxy mit `bluetooth_proxy:` reicht aus
(aktives Verbinden ist nicht nötig). Platziere den ESP32 so, dass er das Fahrzeug empfängt.
Hinweis: Die Home-Assistant-Integration „iBeacon Tracker“ kann dieselben Signale zusätzlich erfassen; beide laufen unabhängig.

## Entwicklung
- Protokoll: [docs/PROTOCOL.md](docs/PROTOCOL.md) · Tests: `python3 -m pytest tests` · Sniffer: `tools/ble_sniff.py`
- Repository: https://github.com/abcklaus/ha-maxsensor-tpms

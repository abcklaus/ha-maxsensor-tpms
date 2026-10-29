# Anleitung: Echte Sensordaten mitschneiden und gegen die App prüfen

Ziel: Sicherstellen, dass die Dekodierung (Druck, Temperatur, Batterie, ID) mit deinen vier Sensoren übereinstimmt.
Die Sensoren senden vermutlich nur, wenn die Räder sich drehen bzw. kurz nach Bewegung – ggf. kurz fahren oder das Rad bewegen.

## Variante A – Mac (unabhängig von Home Assistant)
1. `pip3 install bleak`
2. In den Systemeinstellungen → Datenschutz → Bluetooth das Terminal erlauben.
3. `python3 tools/ble_sniff.py 180` startet einen 3-Minuten-Mitschnitt und schreibt `tools/mitschnitt.csv`.
4. Parallel in der **Multi Wheel-App** (Handy) die angezeigten Werte notieren (Zeit, ID, Druck, Temperatur).
   Hinweis: Handy und Mac dürfen gleichzeitig scannen, die Sensoren sind reine Sender.

## Variante B – Home Assistant mit ESPHome-Proxy
1. Einstellungen → Geräte & Dienste → **Bluetooth** → Konfigurieren → **Advertisement-Monitor**.
   Dort nach Einträgen mit Herstellerdaten `004c` und `0215b54adc0067f911d996690800200c9a6…` suchen (Endung 66, 67 oder 6a).
2. Alternativ Debug-Log der Integration aktivieren (`configuration.yaml`):
   ```yaml
   logger:
     logs:
       custom_components.maxsensor_tpms: debug
   ```
   Pro Advertisement erscheint dann: Sensor-ID, Proxy (`source`), dekodierte Werte **und die Rohdaten (hex)**.
3. Stelle sicher, dass der ESPHome-Proxy Bluetooth-Proxy aktiv hat (`bluetooth_proxy:` mit `active: true` ist für diese
   rein passiven iBeacons nicht nötig).

## Was ich von dir brauche
- Die CSV bzw. 10–20 Zeilen Debug-Log je Rad.
- Die gleichzeitig in der App angezeigten Werte (Druck mit Einheit, Temperatur) und die vier Sensor-IDs aus der App.
Damit gleiche ich Offsets und Skalierung ab (`docs/PROTOCOL.md`) und passe `parser.py` bei Abweichungen an.

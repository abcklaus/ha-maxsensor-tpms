"""Lauscht dauerhaft auf TPMS-iBeacons (lokaler Adapter oder ESPHome-Proxy) und legt neue Sensoren automatisch an."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import logging

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.util import dt as dt_util

from .const import CONF_AUTO_ADD, CONF_IGNORED_IDS, CONF_MANUAL_IDS, CONF_MIN_RSSI, DOMAIN, parse_ids
from .parser import APPLE_COMPANY_ID, UUID_TO_TYPE, parse_manufacturer_data_dict

_LOGGER = logging.getLogger(__name__)


@dataclass
class TPMSState:
    """Zuletzt bekannte Werte eines Sensors."""

    pressure_kpa: float | None = None
    temperature_c: float | None = None
    battery_low: bool | None = None
    rssi: int | None = None
    last_seen: datetime | None = None
    sensor_type: int | None = None


class TPMSCoordinator:
    """Push-basierter Koordinator für alle Sensoren eines Config Entries."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        opts = entry.options
        self.auto_add: bool = opts.get(CONF_AUTO_ADD, True)
        self.min_rssi: int | None = opts.get(CONF_MIN_RSSI)
        self.ignored: set[str] = parse_ids(opts.get(CONF_IGNORED_IDS))

        # Bekannte Sensoren = bereits angelegte Geräte + manuell eingetragene IDs
        registry = dr.async_get(hass)
        known = {
            ident
            for device in dr.async_entries_for_config_entry(registry, entry.entry_id)
            for domain, ident in device.identifiers
            if domain == DOMAIN
        }
        self.states: dict[str, TPMSState] = {
            sid: TPMSState() for sid in (known | parse_ids(opts.get(CONF_MANUAL_IDS))) - self.ignored
        }
        self._listeners: dict[str, set[Callable[[], None]]] = {}
        self._new_listeners: set[Callable[[str], None]] = set()

    # --- Registrierung von Listenern -------------------------------------------------
    @callback
    def async_add_listener(self, sensor_id: str, update_callback: Callable[[], None]) -> CALLBACK_TYPE:
        self._listeners.setdefault(sensor_id, set()).add(update_callback)

        @callback
        def _remove() -> None:
            self._listeners.get(sensor_id, set()).discard(update_callback)

        return _remove

    @callback
    def async_add_new_sensor_listener(self, new_callback: Callable[[str], None]) -> CALLBACK_TYPE:
        self._new_listeners.add(new_callback)

        @callback
        def _remove() -> None:
            self._new_listeners.discard(new_callback)

        return _remove

    @callback
    def async_ignore(self, sensor_ids: set[str]) -> None:
        """Sensor dauerhaft ignorieren (z. B. nach Löschen des Geräts)."""
        self.ignored |= sensor_ids
        for sid in sensor_ids:
            self.states.pop(sid, None)

    # --- Bluetooth -------------------------------------------------------------------
    @callback
    def async_start(self) -> CALLBACK_TYPE:
        """Registriert je iBeacon-UUID einen Callback (läuft, solange der Entry geladen ist)."""
        cancels = [
            bluetooth.async_register_callback(
                self.hass,
                self._handle_advertisement,
                BluetoothCallbackMatcher(
                    manufacturer_id=APPLE_COMPANY_ID,
                    manufacturer_data_start=[0x02, 0x15, *uuid],
                    connectable=False,
                ),
                BluetoothScanningMode.PASSIVE,
            )
            for uuid in UUID_TO_TYPE
        ]

        @callback
        def _cancel() -> None:
            for cancel in cancels:
                cancel()

        return _cancel

    @callback
    def _handle_advertisement(
        self, service_info: BluetoothServiceInfoBleak, change: BluetoothChange
    ) -> None:
        reading = parse_manufacturer_data_dict(service_info.manufacturer_data)
        if reading is None or reading.sensor_id in self.ignored:
            return
        sid = reading.sensor_id

        is_new = sid not in self.states
        if is_new:
            if not self.auto_add:
                return
            if self.min_rssi is not None and service_info.rssi < self.min_rssi:
                _LOGGER.debug("Neuer Sensor %s ignoriert: RSSI %s < %s", sid, service_info.rssi, self.min_rssi)
                return
            _LOGGER.info("Neuer TPMS-Sensor %s erkannt (via %s) – wird automatisch angelegt", sid, service_info.source)
            self.states[sid] = TPMSState()

        _LOGGER.debug(
            "Sensor %s via %s (%s): %s kPa, %s °C, Batterie schwach=%s, RSSI=%s | roh=%s",
            sid, service_info.source, service_info.address, reading.pressure_kpa,
            reading.temperature_c, reading.battery_low, service_info.rssi,
            service_info.manufacturer_data.get(APPLE_COMPANY_ID, b"").hex(),
        )
        data = self.states[sid]
        data.pressure_kpa = reading.pressure_kpa
        if reading.temperature_c is not None:  # bei "Batterie schwach" liefert der Sensor keine Temperatur
            data.temperature_c = reading.temperature_c
        data.battery_low = reading.battery_low
        data.sensor_type = reading.sensor_type
        data.rssi = service_info.rssi
        data.last_seen = dt_util.utcnow()

        if is_new:
            for new_cb in list(self._new_listeners):
                new_cb(sid)
        for listener in list(self._listeners.get(sid, ())):
            listener()

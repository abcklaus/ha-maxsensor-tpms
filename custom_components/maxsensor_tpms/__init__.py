"""MaxSensor TPMS – Reifendrucksensoren (Sysgration "Multi Wheel BLE TPMS") per Bluetooth."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import CONF_IGNORED_IDS, CONF_MANUAL_IDS, DOMAIN, parse_ids
from .coordinator import TPMSCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

type TPMSConfigEntry = ConfigEntry[TPMSCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TPMSConfigEntry) -> bool:
    coordinator = TPMSCoordinator(hass, entry)
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Erst nach dem Anlegen der Entitäten starten, damit kein Advertisement verloren geht
    entry.async_on_unload(coordinator.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TPMSConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: TPMSConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Gerät löschen erlaubt; die Sensor-ID wird ignoriert, damit sie nicht sofort neu angelegt wird."""
    ids = {ident for domain, ident in device_entry.identifiers if domain == DOMAIN}
    options = dict(entry.options)
    options[CONF_IGNORED_IDS] = ",".join(sorted(parse_ids(options.get(CONF_IGNORED_IDS)) | ids))
    options[CONF_MANUAL_IDS] = ",".join(sorted(parse_ids(options.get(CONF_MANUAL_IDS)) - ids))
    hass.config_entries.async_update_entry(entry, options=options)
    entry.runtime_data.async_ignore(ids)
    return True

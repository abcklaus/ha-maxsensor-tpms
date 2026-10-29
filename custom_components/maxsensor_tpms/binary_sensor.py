"""Binärsensor: Batterie des Reifensensors schwach."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import TPMSConfigEntry
from .coordinator import TPMSCoordinator
from .entity import TPMSEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: TPMSConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data

    @callback
    def _add(sensor_id: str) -> None:
        async_add_entities([TPMSBatteryLow(coordinator, sensor_id)])

    for sensor_id in list(coordinator.states):
        _add(sensor_id)
    entry.async_on_unload(coordinator.async_add_new_sensor_listener(_add))


class TPMSBatteryLow(TPMSEntity, BinarySensorEntity, RestoreEntity):
    _attr_device_class = BinarySensorDeviceClass.BATTERY  # on = schwach

    def __init__(self, coordinator: TPMSCoordinator, sensor_id: str) -> None:
        super().__init__(coordinator, sensor_id)
        self._attr_unique_id = f"{sensor_id}_battery_low"
        self._restored: bool | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None and last.state in ("on", "off"):
            self._restored = last.state == "on"

    @property
    def is_on(self) -> bool | None:
        data = self.state_data
        value = data.battery_low if data else None
        return value if value is not None else self._restored

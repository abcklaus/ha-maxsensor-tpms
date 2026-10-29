"""Basis-Entität."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .coordinator import TPMSCoordinator, TPMSState


class TPMSEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: TPMSCoordinator, sensor_id: str) -> None:
        self.coordinator = coordinator
        self.sensor_id = sensor_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, sensor_id)},
            name=f"Reifen {sensor_id}",  # per UI umbenennbar (z. B. "Reifen vorne links")
            manufacturer="Sysgration",
            model="Multi Wheel BLE TPMS",
            serial_number=sensor_id,
        )

    @property
    def state_data(self) -> TPMSState | None:
        return self.coordinator.states.get(self.sensor_id)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.coordinator.async_add_listener(self.sensor_id, self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

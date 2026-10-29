"""Sensoren: Druck, Temperatur, Signalstärke, zuletzt gesehen."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TPMSConfigEntry
from .coordinator import TPMSCoordinator, TPMSState
from .entity import TPMSEntity


@dataclass(frozen=True, kw_only=True)
class TPMSSensorDescription(SensorEntityDescription):
    value_fn: Callable[[TPMSState], float | int | datetime | None]
    restore: bool = True


SENSORS: tuple[TPMSSensorDescription, ...] = (
    TPMSSensorDescription(
        key="pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.KPA,
        suggested_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.pressure_kpa,
    ),
    TPMSSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.temperature_c,
    ),
    TPMSSensorDescription(
        key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.rssi,
        restore=False,
    ),
    TPMSSensorDescription(
        key="last_seen",
        translation_key="last_seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.last_seen,
        restore=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: TPMSConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data

    @callback
    def _add(sensor_id: str) -> None:
        async_add_entities(TPMSSensor(coordinator, sensor_id, desc) for desc in SENSORS)

    for sensor_id in list(coordinator.states):
        _add(sensor_id)
    entry.async_on_unload(coordinator.async_add_new_sensor_listener(_add))


class TPMSSensor(TPMSEntity, RestoreSensor):
    entity_description: TPMSSensorDescription

    def __init__(
        self, coordinator: TPMSCoordinator, sensor_id: str, description: TPMSSensorDescription
    ) -> None:
        super().__init__(coordinator, sensor_id)
        self.entity_description = description
        self._attr_unique_id = f"{sensor_id}_{description.key}"
        self._restored: float | int | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.entity_description.restore and (last := await self.async_get_last_sensor_data()):
            self._restored = last.native_value  # type: ignore[assignment]

    @property
    def native_value(self) -> float | int | datetime | None:
        data = self.state_data
        value = self.entity_description.value_fn(data) if data else None
        return value if value is not None else self._restored

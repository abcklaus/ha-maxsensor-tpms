"""Config Flow: ein einziger "Hub"-Eintrag; Sensoren werden danach automatisch angelegt."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlowWithReload
from homeassistant.core import callback
from homeassistant.helpers.selector import NumberSelector, NumberSelectorConfig, NumberSelectorMode

from .const import (
    CONF_AUTO_ADD,
    CONF_IGNORED_IDS,
    CONF_MANUAL_IDS,
    CONF_MIN_RSSI,
    DOMAIN,
    parse_ids,
)
from .parser import parse_manufacturer_data_dict


class MaxsensorTPMSConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> MaxsensorTPMSOptionsFlow:
        return MaxsensorTPMSOptionsFlow()

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfoBleak) -> ConfigFlowResult:
        if parse_manufacturer_data_dict(discovery_info.manufacturer_data) is None:
            return self.async_abort(reason="not_supported")
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return await self.async_step_user()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="MaxSensor TPMS", data={})
        self._set_confirm_only()
        return self.async_show_form(step_id="user")


def _ids_valid(text: str | None) -> bool:
    import re

    return all(p.upper() in parse_ids(p) for p in re.split(r"[,;\s]+", text or "") if p)


class MaxsensorTPMSOptionsFlow(OptionsFlowWithReload):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not (_ids_valid(user_input.get(CONF_MANUAL_IDS)) and _ids_valid(user_input.get(CONF_IGNORED_IDS))):
                errors["base"] = "invalid_sensor_id"
            else:
                data = dict(user_input)
                for key in (CONF_MANUAL_IDS, CONF_IGNORED_IDS):
                    data[key] = ",".join(sorted(parse_ids(data.get(key))))
                if data.get(CONF_MIN_RSSI) is not None:
                    data[CONF_MIN_RSSI] = int(data[CONF_MIN_RSSI])
                return self.async_create_entry(data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_AUTO_ADD, default=True): bool,
                vol.Optional(CONF_MIN_RSSI): NumberSelector(
                    NumberSelectorConfig(min=-120, max=0, step=1, mode=NumberSelectorMode.BOX, unit_of_measurement="dBm")
                ),
                vol.Optional(CONF_MANUAL_IDS, default=""): str,
                vol.Optional(CONF_IGNORED_IDS, default=""): str,
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(schema, user_input or self.config_entry.options),
            errors=errors,
        )

"""Config flow for bosma integration."""
from __future__ import annotations

import logging

from bleak_retry_connector import BLEDevice
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_ADDRESS

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_KEY, CONF_LOCAL_NAME, CONF_TINY_UID, CONF_SLOT, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_validate_lock_or_error(
    local_name: str, device: BLEDevice, key: str
) -> dict[str, str]:
    """Validate the lock and return errors if any."""
    if len(key) != 32:
        return {CONF_KEY: "invalid_key_format"}
    try:
        bytes.fromhex(key)
    except ValueError:
        return {CONF_KEY: "invalid_key_format"}
    return {}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for bosma."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}
        # self._lock_cfg: ValidatedLockConfig | None = None
        self._reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device."""
        errors: dict[str, str] = {}

        _LOGGER.debug("in async_step_user")

        if user_input is not None:
            self.context["active"] = True
            address = user_input[CONF_ADDRESS]
            discovery_info = self._discovered_devices[address]
            local_name = discovery_info.name
            key = user_input[CONF_KEY]
            tiny_uid = user_input[CONF_TINY_UID]
            await self.async_set_unique_id(
                discovery_info.address, raise_on_progress=False
            )
            self._abort_if_unique_id_configured()
            if not (
                errors := await async_validate_lock_or_error(
                    local_name, discovery_info.device, key
                )
            ):
                return self.async_create_entry(
                    title=local_name,
                    data={
                        CONF_LOCAL_NAME: discovery_info.name,
                        CONF_ADDRESS: discovery_info.address,
                        CONF_KEY: key,
                        CONF_TINY_UID: tiny_uid,
                    },
                )

        if discovery := self._discovery_info:
            _LOGGER.debug("self._discovery_info")
            self._discovered_devices[discovery.address] = discovery
        else:
            _LOGGER.debug("else self._discovery_info")
            current_addresses = self._async_current_ids()
            current_unique_names = {
                entry.data.get(CONF_LOCAL_NAME)
                for entry in self._async_current_entries()
                # if local_name_is_unique(entry.data.get(CONF_LOCAL_NAME))
            }
            for discovery in async_discovered_service_info(self.hass):
                if (
                    discovery.address in current_addresses
                    or discovery.name in current_unique_names
                    or discovery.address in self._discovered_devices
                ):
                    continue
                self._discovered_devices[discovery.address] = discovery

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): vol.In(
                    {
                        service_info.address: (
                            f"{service_info.name} ({service_info.address})"
                        )
                        for service_info in self._discovered_devices.values()
                    }
                ),
                vol.Required(CONF_KEY): str,
                vol.Required(CONF_TINY_UID): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

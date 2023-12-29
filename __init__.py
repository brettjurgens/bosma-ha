"""The bosma integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.bluetooth import async_ble_device_from_address
import logging
from bosma import AegisLock
from homeassistant.core import Event, HomeAssistant, callback
from .const import (
    CONF_KEY,
    CONF_LOCAL_NAME,
    CONF_TINY_UID,
    DOMAIN,
)
from homeassistant.exceptions import ConfigEntryNotReady

from homeassistant.const import CONF_ADDRESS, EVENT_HOMEASSISTANT_STOP, Platform
from .model import BosmaData

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.LOCK, Platform.SENSOR]


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up bosma from a config entry."""

    local_name = entry.data[CONF_LOCAL_NAME]
    address = entry.data[CONF_ADDRESS]
    key = entry.data[CONF_KEY]
    tiny_uid = entry.data[CONF_TINY_UID]

    aegis_lock = AegisLock(
        bytes.fromhex(key),
        tiny_uid,
    )

    ble_device = async_ble_device_from_address(hass, address)

    if ble_device is None:
        _LOGGER.debug(f"BLE Device not present")
        raise ConfigEntryNotReady("BLEDevice not found")

    try:
        _LOGGER.debug(f"Connecting to the lock at address: {ble_device.address}")
        await aegis_lock.connect(ble_device, keep_alive=True)
        _LOGGER.debug(f"Lock connected!")
    except Exception as ex:
        raise ConfigEntryNotReady(f"{ex}; Error connecting to Bosma lock.") from ex

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = BosmaData(
        entry.title, aegis_lock
    )

    @callback
    async def _async_shutdown(event: Event | None = None) -> None:
        await aegis_lock.disconnect()

    entry.async_on_unload(_async_shutdown)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_shutdown)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import format_mac
from homeassistant.components import bluetooth
from homeassistant.core import callback

from .model import BosmaData
from .const import DOMAIN

from bosma.model import Connectivity, LockState
import logging

_LOGGER = logging.getLogger(__name__)


class BosmaEntity(Entity):
    _attr_should_poll = False

    def __init__(self, data: BosmaData) -> None:
        self._data = data
        self._device = data.lock
        address = self._device.address()
        if not self._attr_unique_id:
            self._attr_unique_id = format_mac(address)

        self._attr_device_info = DeviceInfo(
            name=data.title,
            manufacturer="Bosma",
            model="Aegis",
            connections={(dr.CONNECTION_BLUETOOTH, address)},
            identifiers={(DOMAIN, format_mac(address))},
        )
        self._attr_available = False
        if self._device.state:
            self._async_update_state(self._device.state, self._device.is_connected())

    @callback
    def _async_update_state(
        self, new_state: LockState, connectivity: Connectivity
    ) -> None:
        """Update the state."""
        _LOGGER.debug("_async_update_state")
        self._attr_available = True

    @callback
    def _async_state_changed(
        self, new_state: LockState, connectivity: Connectivity
    ) -> None:
        """Handle state changed."""
        self._async_update_state(new_state, connectivity)
        self.async_write_ha_state()

    @callback
    def _async_device_unavailable(
        self, _service_info: bluetooth.BluetoothServiceInfoBleak
    ) -> None:
        """Handle device not longer being seen by the bluetooth stack."""
        self._attr_available = False
        _LOGGER.debug("_async_device_unavailable")
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            bluetooth.async_track_unavailable(
                self.hass, self._async_device_unavailable, self._device.address
            )
        )
        self.async_on_remove(self._device.register_callback(self._async_state_changed))
        return await super().async_added_to_hass()

    async def async_update(self) -> None:
        """Request a manual update."""
        await self._device.update()

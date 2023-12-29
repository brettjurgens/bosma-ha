from bosma.model import LockState, DoorStatus, Connectivity
from .entity import BosmaEntity
from homeassistant.helpers.device_registry import format_mac
from .model import BosmaData
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up door sensor."""
    data: BosmaData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BosmaAegisDoorSensor(data), BosmaAegisConnectedSensor(data)])


class BosmaAegisDoorSensor(BinarySensorEntity, BosmaEntity):
    _attr_device_class = BinarySensorDeviceClass.DOOR
    _attr_name = "Opening"

    def __init__(self, data: BosmaData) -> None:
        self._attr_unique_id = f"{format_mac(data.lock.address())}.opening"
        super().__init__(data)

    @callback
    def _async_update_state(
        self, new_state: LockState, connectivity: Connectivity
    ) -> None:
        """Update the state."""
        self._attr_is_on = new_state.door == DoorStatus.OPEN

        super()._async_update_state(new_state, connectivity)


class BosmaAegisConnectedSensor(BinarySensorEntity, BosmaEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_name = "Connection"

    def __init__(self, data: BosmaData) -> None:
        self._attr_unique_id = f"{format_mac(data.lock.address())}.connectivity"
        super().__init__(data)

    @callback
    def _async_update_state(
        self, new_state: LockState, connectivity: Connectivity
    ) -> None:
        """Update the state."""
        self._attr_is_on = connectivity == Connectivity.CONNECTED
        _LOGGER.debug(f"connected update: {connectivity}")
        super()._async_update_state(new_state, connectivity)

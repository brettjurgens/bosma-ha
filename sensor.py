from homeassistant.helpers.device_registry import format_mac
from bosma.model import LockState, Connectivity
from .entity import BosmaEntity
from .model import BosmaData
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
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
    async_add_entities([BosmaAegisBatterySensor(data)])


class BosmaAegisBatterySensor(BosmaEntity, SensorEntity):
    entity_description = SensorEntityDescription(
        "battery_level",
        name="Battery Level",
        device_class=SensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        has_entity_name=True,
        native_unit_of_measurement=PERCENTAGE,
    )

    def __init__(self, data: BosmaData) -> None:
        self._attr_unique_id = f"{format_mac(data.lock.address())}.battery_level"
        super().__init__(data)

    @callback
    def _async_update_state(
        self, new_state: LockState, connectivity: Connectivity
     ) -> None:
        """Update the state."""
        _LOGGER.debug(f"battery update: {new_state.battery}")
        self._attr_native_value = new_state.battery

        super()._async_update_state(new_state, connectivity)

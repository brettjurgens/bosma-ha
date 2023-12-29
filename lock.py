from homeassistant.components.lock import LockEntity
from bosma.model import LockState, LockedStatus, Connectivity
from .entity import BosmaEntity
from .model import BosmaData
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up locks."""
    data: BosmaData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BosmaAegisLock(data)])


class BosmaAegisLock(BosmaEntity, LockEntity):
    _attr_name = "Lock"

    @callback
    def _async_update_state(
        self, new_state: LockState, connectivity: Connectivity
    ) -> None:
        """Update the state."""
        self._attr_is_locked = new_state.lock == LockedStatus.LOCK
        self._attr_is_locking = False
        self._attr_is_unlocking = False
        self._attr_is_jammed = False

        super()._async_update_state(new_state, connectivity)

    async def async_unlock(self):
        self._attr_is_unlocking = True
        self.async_write_ha_state()
        await self._device.unlock()

    async def async_lock(self):
        self._attr_is_locking = True
        self.async_write_ha_state()
        await self._device.lock()

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN, KEY_DEVICE_ACTIVE
from .device import build_device_info, combined_data, flatten, get_system_name


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    client = data[DATA_CLIENT]
    coordinator = data[DATA_COORDINATOR]
    async_add_entities([AeroplusPowerSwitch(client, coordinator, entry)])


class AeroplusPowerSwitch(CoordinatorEntity, SwitchEntity):
    """On/off control for the Aeroplus WRG device.

    Intentionally the only control this integration exposes: all other modes
    (auto mode, fan speed, etc.) are meant to be managed with the Siegenia app.
    """

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, client, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        system_name = get_system_name(coordinator.data)
        self._attr_name = f"{system_name} Power" if system_name else "Aeroplus WRG Power"
        self._attr_unique_id = f"{entry.entry_id}-power"

    @property
    def device_info(self):
        return build_device_info(self.coordinator.data, self._entry.entry_id, self._entry.data.get("host"))

    @property
    def is_on(self) -> bool:
        flat = flatten(combined_data(self.coordinator.data))
        return bool(flat.get(KEY_DEVICE_ACTIVE))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._client.set_device_active(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._client.set_device_active(False)
        await self.coordinator.async_request_refresh()

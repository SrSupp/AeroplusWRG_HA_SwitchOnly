from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN, KEY_AUTOMODE, KEY_DEVICE_ACTIVE
from .device import OptimisticStateMixin, build_device_info, combined_data, flatten, get_system_name


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    client = data[DATA_CLIENT]
    coordinator = data[DATA_COORDINATOR]
    async_add_entities(
        [
            AeroplusPowerSwitch(client, coordinator, entry),
            AeroplusAutoModeSwitch(client, coordinator, entry),
        ]
    )


class AeroplusPowerSwitch(OptimisticStateMixin, CoordinatorEntity, SwitchEntity):
    """On/off control for the Aeroplus WRG device."""

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
        actual = bool(flat.get(KEY_DEVICE_ACTIVE))
        return self._resolve_optimistic(actual)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._client.set_device_active(True)
        self._set_optimistic(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._client.set_device_active(False)
        self._set_optimistic(False)
        await self.coordinator.async_request_refresh()


class AeroplusAutoModeSwitch(OptimisticStateMixin, CoordinatorEntity, SwitchEntity):
    """Automatic mode. This is a genuinely separate boolean field
    ("automode") from fanmode, confirmed against a live device's
    getDeviceParams response - fanmode never takes an "AUTO" value here."""

    _attr_icon = "mdi:fan-auto"

    def __init__(self, client, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        system_name = get_system_name(coordinator.data)
        self._attr_name = f"{system_name} Automatikmodus" if system_name else "Aeroplus WRG Automatikmodus"
        self._attr_unique_id = f"{entry.entry_id}-automode"

    @property
    def device_info(self):
        return build_device_info(self.coordinator.data, self._entry.entry_id, self._entry.data.get("host"))

    @property
    def is_on(self) -> bool:
        flat = flatten(combined_data(self.coordinator.data))
        actual = bool(flat.get(KEY_AUTOMODE))
        return self._resolve_optimistic(actual)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._client.set_device_params({KEY_AUTOMODE: True})
        self._set_optimistic(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._client.set_device_params({KEY_AUTOMODE: False})
        self._set_optimistic(False)
        await self.coordinator.async_request_refresh()

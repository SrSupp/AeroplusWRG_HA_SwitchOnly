from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DATA_SPEED_MEMORY,
    DOMAIN,
    KEY_AUTOMODE,
    KEY_AUTOMODE_MAX_AIRFLOW,
    KEY_DEVICE_ACTIVE,
    KEY_FAN_POWER,
)
from .device import OptimisticStateMixin, build_device_info, combined_data, flatten, get_system_name


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    client = data[DATA_CLIENT]
    coordinator = data[DATA_COORDINATOR]
    speed_memory = data[DATA_SPEED_MEMORY]
    async_add_entities(
        [
            AeroplusPowerSwitch(client, coordinator, entry),
            AeroplusAutoModeSwitch(client, coordinator, entry, speed_memory),
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
    getDeviceParams response - fanmode never takes an "AUTO" value here.

    Also restores the last speed value remembered for the mode being entered
    (see device.FanSpeedMemory / number.py), so hopping between
    Automatikmodus and manual mode doesn't lose the speed that was last set
    for each.
    """

    _attr_icon = "mdi:fan-auto"

    def __init__(self, client, coordinator, entry: ConfigEntry, speed_memory) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._speed_memory = speed_memory
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
        params: dict[str, Any] = {KEY_AUTOMODE: True}
        remembered = self._speed_memory.value_for(KEY_AUTOMODE_MAX_AIRFLOW)
        if remembered is not None:
            params[KEY_AUTOMODE_MAX_AIRFLOW] = remembered
        await self._client.set_device_params(params)
        self._set_optimistic(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        params: dict[str, Any] = {KEY_AUTOMODE: False}
        remembered = self._speed_memory.value_for(KEY_FAN_POWER)
        if remembered is not None:
            params[KEY_FAN_POWER] = remembered
        await self._client.set_device_params(params)
        self._set_optimistic(False)
        await self.coordinator.async_request_refresh()

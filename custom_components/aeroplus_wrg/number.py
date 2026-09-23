from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DATA_SPEED_MEMORY,
    DOMAIN,
    KEY_AUTOMODE,
    KEY_AUTOMODE_MAX_AIRFLOW,
    KEY_FAN_POWER,
)
from .device import build_device_info, combined_data, flatten, get_system_name


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    client = data[DATA_CLIENT]
    coordinator = data[DATA_COORDINATOR]
    speed_memory = data[DATA_SPEED_MEMORY]
    async_add_entities([AeroplusFanSpeedNumber(client, coordinator, entry, speed_memory)])


class AeroplusFanSpeedNumber(CoordinatorEntity, NumberEntity):
    """Target fan speed in %.

    While Automatikmodus is on, this controls automode_maxairflow (the cap
    the automatic mode is allowed to reach); otherwise it controls fanpower
    (the manual target speed) - one slider that follows whichever field is
    actually in effect, instead of two separate always-visible entities.
    """

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_mode = "slider"
    _attr_icon = "mdi:fan"

    def __init__(self, client, coordinator, entry: ConfigEntry, speed_memory) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._speed_memory = speed_memory
        system_name = get_system_name(coordinator.data)
        self._attr_name = f"{system_name} Lüftungsgeschwindigkeit" if system_name else "Aeroplus WRG Lüftungsgeschwindigkeit"
        self._attr_unique_id = f"{entry.entry_id}-fanspeed"

    @property
    def device_info(self):
        return build_device_info(self.coordinator.data, self._entry.entry_id, self._entry.data.get("host"))

    def _active_key(self) -> str:
        flat = flatten(combined_data(self.coordinator.data))
        return KEY_AUTOMODE_MAX_AIRFLOW if flat.get(KEY_AUTOMODE) else KEY_FAN_POWER

    @property
    def native_value(self) -> float | None:
        value = flatten(combined_data(self.coordinator.data)).get(self._active_key())
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        key = self._active_key()
        target = int(round(value))
        await self._client.set_device_params({key: target})
        await self._speed_memory.remember(key, target)
        await self.coordinator.async_request_refresh()

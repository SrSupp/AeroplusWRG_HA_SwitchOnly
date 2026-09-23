from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
    KEY_AUTOMODE_MAX_AIRFLOW,
    KEY_FAN_POWER,
)
from .device import build_device_info, combined_data, flatten, get_first, get_system_name


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    client = data[DATA_CLIENT]
    coordinator = data[DATA_COORDINATOR]
    async_add_entities(
        [
            AeroplusPercentNumber(
                client, coordinator, entry, "fanspeed", "Lüftungsgeschwindigkeit", KEY_FAN_POWER, "mdi:fan"
            ),
            AeroplusPercentNumber(
                client,
                coordinator,
                entry,
                "automode-maxairflow",
                "AutomatikGeschwindigkeit",
                KEY_AUTOMODE_MAX_AIRFLOW,
                "mdi:fan-auto",
            ),
        ]
    )


class AeroplusPercentNumber(CoordinatorEntity, NumberEntity):
    """A 0-100% device parameter, settable via setDeviceParams."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_mode = "slider"

    def __init__(self, client, coordinator, entry: ConfigEntry, slug: str, label: str, key: str, icon: str) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._key = key
        self._attr_icon = icon
        system_name = get_system_name(coordinator.data)
        self._attr_name = f"{system_name} {label}" if system_name else f"Aeroplus WRG {label}"
        self._attr_unique_id = f"{entry.entry_id}-{slug}"

    @property
    def device_info(self):
        return build_device_info(self.coordinator.data, self._entry.entry_id, self._entry.data.get("host"))

    @property
    def native_value(self) -> float | None:
        value = get_first(flatten(combined_data(self.coordinator.data)), [self._key])
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self._client.set_device_params({self._key: int(round(value))})
        await self.coordinator.async_request_refresh()

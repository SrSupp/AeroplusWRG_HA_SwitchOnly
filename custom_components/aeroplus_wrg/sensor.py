from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION, PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    KEY_FAN_POWER,
    KEYS_CO2,
    KEYS_TEMPERATURE_INDOOR,
    KEYS_TEMPERATURE_OUTDOOR,
)
from .device import build_device_info, combined_data, flatten, get_first, get_system_name, is_device_active


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities: list[SensorEntity] = [
        AeroplusTemperatureSensor(coordinator, entry, "indoor", "Indoor Temperature", KEYS_TEMPERATURE_INDOOR),
        AeroplusTemperatureSensor(coordinator, entry, "outdoor", "Outdoor Temperature", KEYS_TEMPERATURE_OUTDOOR),
        AeroplusCo2Sensor(coordinator, entry),
        AeroplusFanSpeedFeedbackSensor(coordinator, entry),
    ]
    async_add_entities(entities)


class _AeroplusBaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry: ConfigEntry, slug: str, label: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        system_name = get_system_name(coordinator.data)
        self._attr_name = f"{system_name} {label}" if system_name else f"Aeroplus WRG {label}"
        self._attr_unique_id = f"{entry.entry_id}-{slug}"

    @property
    def device_info(self):
        return build_device_info(self.coordinator.data, self._entry.entry_id, self._entry.data.get("host"))

    def _flat(self) -> dict[str, Any]:
        return flatten(combined_data(self.coordinator.data))


class AeroplusTemperatureSensor(_AeroplusBaseSensor):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, entry: ConfigEntry, slug: str, label: str, keys: list[str]) -> None:
        super().__init__(coordinator, entry, slug, label)
        self._keys = keys

    @property
    def native_value(self) -> float | None:
        return get_first(self._flat(), self._keys)


class AeroplusCo2Sensor(_AeroplusBaseSensor):
    """CO2 reading is only meaningful while air is actually being sampled, so
    this goes unavailable rather than showing a frozen/stale value once the
    device is switched off."""

    _attr_device_class = SensorDeviceClass.CO2
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "co2", "CO2")

    @property
    def available(self) -> bool:
        return super().available and is_device_active(self.coordinator.data)

    @property
    def native_value(self) -> float | None:
        return get_first(self._flat(), KEYS_CO2)


class AeroplusFanSpeedFeedbackSensor(_AeroplusBaseSensor):
    """Read-only feedback of the fan's actual current speed (fanpower), as
    reported by the device - independent of whether it was set manually or by
    automatic mode. Reads as 0% while the device is off, since fanpower then
    still reports its last active value instead of 0."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "fanspeed-feedback", "Feedback Lüftergeschwindigkeit")

    @property
    def native_value(self) -> float | None:
        if not is_device_active(self.coordinator.data):
            return 0
        return get_first(self._flat(), [KEY_FAN_POWER])

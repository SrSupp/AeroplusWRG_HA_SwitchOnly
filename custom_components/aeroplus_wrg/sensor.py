from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN, KEYS_CO2, KEYS_TEMPERATURE_INDOOR, KEYS_TEMPERATURE_OUTDOOR
from .device import build_device_info, combined_data, flatten, get_first, get_system_name


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities: list[SensorEntity] = [
        AeroplusTemperatureSensor(coordinator, entry, "indoor", "Indoor Temperature", KEYS_TEMPERATURE_INDOOR),
        AeroplusTemperatureSensor(coordinator, entry, "outdoor", "Outdoor Temperature", KEYS_TEMPERATURE_OUTDOOR),
        AeroplusCo2Sensor(coordinator, entry),
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
    _attr_device_class = SensorDeviceClass.CO2
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "co2", "CO2")

    @property
    def native_value(self) -> float | None:
        return get_first(self._flat(), KEYS_CO2)

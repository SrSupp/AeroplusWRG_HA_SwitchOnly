from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN, FAN_MODE_LABELS, KEY_FAN_MODE
from .device import build_device_info, combined_data, flatten, get_system_name

FAN_MODE_CODES = {label: code for code, label in FAN_MODE_LABELS.items()}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    client = data[DATA_CLIENT]
    coordinator = data[DATA_COORDINATOR]
    async_add_entities([AeroplusFanModeSelect(client, coordinator, entry)])


class AeroplusFanModeSelect(CoordinatorEntity, SelectEntity):
    """Ventilation mode: air direction (Zuluft/Abluft/Zu-Abluft, with or
    without heat recovery) or fully automatic operation."""

    _attr_icon = "mdi:air-conditioner"
    _attr_options = list(FAN_MODE_LABELS.values())

    def __init__(self, client, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        system_name = get_system_name(coordinator.data)
        self._attr_name = f"{system_name} Lüftungsmodus" if system_name else "Aeroplus WRG Lüftungsmodus"
        self._attr_unique_id = f"{entry.entry_id}-fanmode"

    @property
    def device_info(self):
        return build_device_info(self.coordinator.data, self._entry.entry_id, self._entry.data.get("host"))

    @property
    def current_option(self) -> str | None:
        raw = flatten(combined_data(self.coordinator.data)).get(KEY_FAN_MODE)
        return FAN_MODE_LABELS.get(raw)

    async def async_select_option(self, option: str) -> None:
        raw = FAN_MODE_CODES.get(option)
        if raw is None:
            return
        await self._client.set_device_params({KEY_FAN_MODE: raw})
        await self.coordinator.async_request_refresh()

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_MANUAL_FAN_MODE,
    DOMAIN,
    FAN_MODE_AUTO,
    FAN_MODE_LABELS,
    KEY_DEVICE_ACTIVE,
    KEY_FAN_MODE,
)
from .device import (
    OptimisticStateMixin,
    build_device_info,
    combined_data,
    flatten,
    get_system_name,
)


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
    """Quick on/off for automatic mode.

    The device has no separate "auto mode" flag: automatic operation is just
    one value ("AUTO") of the fanmode field (see select.py for the full set
    of modes). This switch is a convenience shortcut that flips fanmode
    between AUTO and the last manual mode that was actually in use.
    """

    _attr_icon = "mdi:fan-auto"

    def __init__(self, client, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._last_manual_mode = DEFAULT_MANUAL_FAN_MODE
        system_name = get_system_name(coordinator.data)
        self._attr_name = f"{system_name} Automatikmodus" if system_name else "Aeroplus WRG Automatikmodus"
        self._attr_unique_id = f"{entry.entry_id}-automode"

    @property
    def device_info(self):
        return build_device_info(self.coordinator.data, self._entry.entry_id, self._entry.data.get("host"))

    def _handle_coordinator_update(self) -> None:
        raw = flatten(combined_data(self.coordinator.data)).get(KEY_FAN_MODE)
        if raw and raw != FAN_MODE_AUTO and raw in FAN_MODE_LABELS:
            self._last_manual_mode = raw
        super()._handle_coordinator_update()

    @property
    def is_on(self) -> bool:
        flat = flatten(combined_data(self.coordinator.data))
        actual = flat.get(KEY_FAN_MODE) == FAN_MODE_AUTO
        return self._resolve_optimistic(actual)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._client.set_device_params({KEY_FAN_MODE: FAN_MODE_AUTO})
        self._set_optimistic(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._client.set_device_params({KEY_FAN_MODE: self._last_manual_mode})
        self._set_optimistic(False)
        await self.coordinator.async_request_refresh()

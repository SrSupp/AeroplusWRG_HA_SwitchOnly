from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.storage import Store

from .const import DOMAIN, KEY_AUTOMODE_MAX_AIRFLOW, KEY_DEVICE_ACTIVE, KEY_FAN_POWER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

SPEED_MEMORY_STORAGE_VERSION = 1

# How long a just-commanded value is shown optimistically before falling back
# to whatever the coordinator actually reports, in case the command silently
# failed.
OPTIMISTIC_TIMEOUT_SECONDS = 20


class OptimisticStateMixin:
    """Show a just-commanded value immediately, until the coordinator's data
    confirms it (or the timeout above elapses).

    The device needs a moment to actually apply a setDeviceParams call, so
    reading state right back after sending one often returns the still-stale
    value - without this, entities would flash back to the old value for a
    few seconds after every command.
    """

    _optimistic_value: Any = None
    _optimistic_expires: float = 0.0

    def _resolve_optimistic(self, actual: Any) -> Any:
        if self._optimistic_value is not None:
            if actual == self._optimistic_value or time.monotonic() > self._optimistic_expires:
                self._optimistic_value = None
            else:
                return self._optimistic_value
        return actual

    def _set_optimistic(self, value: Any) -> None:
        self._optimistic_value = value
        self._optimistic_expires = time.monotonic() + OPTIMISTIC_TIMEOUT_SECONDS
        self.async_write_ha_state()


class FanSpeedMemory:
    """Remembers the last fan speed value set for each mode (manual fanpower
    vs automatic automode_maxairflow) so that toggling Automatikmodus
    restores whatever was last configured for the mode being entered,
    instead of leaving it at whatever value that field currently happens to
    hold on the device. Persisted via Home Assistant's storage helper, so it
    survives restarts.
    """

    def __init__(self, store: Store, initial: dict[str, int] | None = None) -> None:
        self._store = store
        self._values: dict[str, int] = dict(initial or {})

    @staticmethod
    def _storage_key(entry_id: str) -> str:
        return f"{DOMAIN}_{entry_id}_speed_memory"

    @classmethod
    async def async_load(cls, hass: "HomeAssistant", entry_id: str) -> "FanSpeedMemory":
        store = Store(hass, SPEED_MEMORY_STORAGE_VERSION, cls._storage_key(entry_id))
        data = await store.async_load()
        return cls(store, data if isinstance(data, dict) else None)

    @classmethod
    async def async_remove(cls, hass: "HomeAssistant", entry_id: str) -> None:
        await Store(hass, SPEED_MEMORY_STORAGE_VERSION, cls._storage_key(entry_id)).async_remove()

    def value_for(self, key: str) -> int | None:
        return self._values.get(key)

    async def remember(self, key: str, value: int) -> None:
        if key not in (KEY_FAN_POWER, KEY_AUTOMODE_MAX_AIRFLOW):
            return
        self._values[key] = value
        await self._store.async_save(self._values)


def _info_from_data(data: dict | None) -> dict:
    info = (data or {}).get("info") or {}
    return info if isinstance(info, dict) else {}


def _coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def combined_data(data: dict | None) -> dict[str, Any]:
    """Merge state/params/info into a single flat-ish dict (later parts win)."""
    merged: dict[str, Any] = {}
    for part in ("state", "params", "info"):
        d = (data or {}).get(part) or {}
        if isinstance(d, dict):
            merged.update(d)
    return merged


def flatten(data: dict[str, Any]) -> dict[str, Any]:
    """Flatten nested dicts into dot-separated keys, e.g. {'airbase': {'co2': 1}}
    becomes {'airbase.co2': 1}. Top-level keys are kept as well."""
    out: dict[str, Any] = {}

    def _walk(d: dict[str, Any], parent: str) -> None:
        for key, value in d.items():
            path = f"{parent}.{key}" if parent else str(key)
            if isinstance(value, dict):
                _walk(value, path)
            else:
                out[path] = value

    _walk(data, "")
    out.update(data)
    return out


def get_first(flat: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in flat and flat[key] is not None:
            return flat[key]
    return None


def get_system_name(data: dict | None) -> str | None:
    flat = flatten(combined_data(data))
    return get_first(flat, ["systemname", "devicename", "device_name"])


def is_device_active(data: dict | None) -> bool:
    return bool(flatten(combined_data(data)).get(KEY_DEVICE_ACTIVE))


def build_device_info(data: dict | None, entry_id: str, host: str | None = None) -> dict:
    info = _info_from_data(data)
    serial_raw = info.get("serialnr") or info.get("serial_number")
    identifiers = {(DOMAIN, str(serial_raw))} if serial_raw else {(DOMAIN, entry_id)}

    device_info: dict[str, Any] = {
        "identifiers": identifiers,
        "manufacturer": "Siegenia",
    }

    name = get_system_name(data)
    if not name and host:
        name = f"Aeroplus WRG {host}"
    if name:
        device_info["name"] = name

    model = _coerce_str(info.get("model") or info.get("type") or info.get("hardwareversion"))
    if model:
        device_info["model"] = model

    sw_version = _coerce_str(info.get("softwareversion"))
    if sw_version:
        device_info["sw_version"] = sw_version

    hw_version = _coerce_str(info.get("hardwareversion"))
    if hw_version:
        device_info["hw_version"] = hw_version

    serial = _coerce_str(serial_raw)
    if serial:
        device_info["serial_number"] = serial

    return device_info

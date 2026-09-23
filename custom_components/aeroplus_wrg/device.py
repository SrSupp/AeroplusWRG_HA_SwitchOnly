from __future__ import annotations

from typing import Any

from .const import DOMAIN


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

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import SiegeniaClient
from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DATA_SPEED_MEMORY,
    DOMAIN,
    PLATFORMS,
    UPDATE_INTERVAL_SECONDS,
)
from .device import FanSpeedMemory, build_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aeroplus WRG from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data["host"]
    username = entry.data["username"]
    password = entry.data["password"]
    port = entry.data.get("port", 443)
    use_ssl = entry.data.get("use_ssl", True)

    client = SiegeniaClient(
        host=host,
        username=username,
        password=password,
        port=port,
        use_ssl=use_ssl,
    )
    await client.connect()

    async def _async_update() -> dict:
        try:
            if not client.connected:
                await client.connect()
            state = await client.get_device_state()
            params = await client.get_device_params()
            info = await client.get_device()
        except Exception as exc:
            # reconnect + retry once
            _LOGGER.debug("Update error, attempting reconnect: %s", exc)
            await client.connect()
            state = await client.get_device_state()
            params = await client.get_device_params()
            info = await client.get_device()
        return {"state": state, "params": params, "info": info}

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_async_update,
        update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
    )

    await coordinator.async_config_entry_first_refresh()

    device_registry = dr.async_get(hass)
    device_info = build_device_info(coordinator.data, entry.entry_id, host)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers=device_info["identifiers"],
        manufacturer=device_info.get("manufacturer"),
        name=device_info.get("name"),
        model=device_info.get("model"),
        sw_version=device_info.get("sw_version"),
        hw_version=device_info.get("hw_version"),
        serial_number=device_info.get("serial_number"),
    )

    # Push-triggered refresh when unsolicited WS messages arrive.
    client.set_on_push(lambda _data: hass.async_create_task(coordinator.async_request_refresh()))

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_COORDINATOR: coordinator,
        DATA_SPEED_MEMORY: FanSpeedMemory(),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if data:
            client: SiegeniaClient | None = data.get(DATA_CLIENT)
            if client:
                await client.close()
    return unload_ok

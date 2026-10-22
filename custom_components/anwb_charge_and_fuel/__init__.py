"""
ANWB Charge & Fuel
Entry points for the Home Assistant integration.
"""

import logging
from typing import Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import RouteCoordinator

DOMAIN = "anwb_charge_and_fuel"
PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("anwb_charge_and_fuel: async_setup completed")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    entry_data = hass.data[DOMAIN].setdefault(entry.entry_id, {})
    entry_data["entry"] = entry

    coordinator = entry_data.get("coordinator")
    if coordinator is None:
        coordinator = RouteCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        entry_data["coordinator"] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    hass.data[DOMAIN].pop(entry.entry_id, None)

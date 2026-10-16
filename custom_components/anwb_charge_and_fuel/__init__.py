"""
ANWB Charge & Fuel
Entry points for the Home Assistant integration (minimal skeleton).
"""

import logging
from typing import Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "anwb_charge_and_fuel"
PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("anwb_charge_and_fuel: async_setup completed")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})
    hass.data[DOMAIN][entry.entry_id]["entry"] = entry

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    hass.data[DOMAIN].pop(entry.entry_id, None)

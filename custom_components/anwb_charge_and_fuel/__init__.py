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

PLATFORMS = [
    "sensor",
    "select",
    "number",
    "button",
]

_LOGGER = logging.getLogger(__name__)


async def async_setup(
    hass: HomeAssistant,
    config: Dict,
) -> bool:
    """Set up the integration."""

    hass.data.setdefault(DOMAIN, {})

    _LOGGER.debug(
        "anwb_charge_and_fuel: async_setup completed"
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up ANWB Charge & Fuel from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    entry_data = hass.data[DOMAIN].setdefault(
        entry.entry_id,
        {},
    )

    entry_data["entry"] = entry

    coordinator = entry_data.get("coordinator")

    if coordinator is None:
        coordinator = RouteCoordinator(
            hass,
            entry,
        )

        await coordinator.async_config_entry_first_refresh()

        entry_data["coordinator"] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    _LOGGER.debug(
        "ANWB Charge & Fuel loaded for entry %s",
        entry.entry_id,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        hass.data[DOMAIN].pop(
            entry.entry_id,
            None,
        )

    return unload_ok


async def async_remove_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Handle removal of a config entry."""

    hass.data[DOMAIN].pop(
        entry.entry_id,
        None,
    )

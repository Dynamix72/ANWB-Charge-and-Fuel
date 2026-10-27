"""
Button entities for ANWB Charge & Fuel.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        [
            ANWBRefreshButton(coordinator),
            ANWBUpdateLocationButton(coordinator),
        ]
    )


class ANWBRefreshButton(
    CoordinatorEntity,
    ButtonEntity,
):
    """Refresh ANWB data."""

    _attr_name = "Gegevens ophalen"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator):
        """Initialize button."""
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_refresh"
        )

    async def async_press(self) -> None:
        """Refresh data."""
        await self.coordinator.async_request_refresh()


class ANWBUpdateLocationButton(
    CoordinatorEntity,
    ButtonEntity,
):
    """Update device tracker location."""

    _attr_name = "Locatie vernieuwen"
    _attr_icon = "mdi:crosshairs-gps"

    def __init__(self, coordinator):
        """Initialize button."""
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_update_location"
        )

    async def async_press(self) -> None:
        """Update location and refresh."""

        #
        # In de huidige versie doet de coordinator
        # bij iedere refresh opnieuw een uitlezing
        # van het device_tracker entity.
        #
        # Daarom is een refresh voldoende.
        #

        await self.coordinator.async_request_refresh()


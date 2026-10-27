"""
Button entities for ANWB Charge & Fuel.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
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


class ANWBBaseButton(
    CoordinatorEntity,
    ButtonEntity,
):
    """Base button."""

    _attr_entity_category = (
        EntityCategory.CONFIG
    )

    @property
    def device_info(self):
        """Return device information."""

        return DeviceInfo(
            identifiers={
                (DOMAIN, "settings")
            },
            name="ANWB Settings",
            manufacturer="ANWB",
        )


class ANWBRefreshButton(
    ANWBBaseButton,
):
    """Refresh ANWB data."""

    _attr_name = "Gegevens ophalen"
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        coordinator,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}"
            "_refresh"
        )

    async def async_press(
        self,
    ) -> None:
        """Refresh data."""

        await self.coordinator.async_request_refresh()


class ANWBUpdateLocationButton(
    ANWBBaseButton,
):
    """Update location."""

    _attr_name = "Locatie vernieuwen"
    _attr_icon = "mdi:crosshairs-gps"

    def __init__(
        self,
        coordinator,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}"
            "_update_location"
        )

    async def async_press(
        self,
    ) -> None:
        """Refresh tracker data."""

        await self.coordinator.async_request_refresh()

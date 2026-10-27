"""
Text entities for ANWB Charge & Fuel.
"""

from __future__ import annotations

from homeassistant.components.text import TextEntity
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
    """Set up text entities."""

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        [
            ANWBDestinationText(
                coordinator
            )
        ]
    )


class ANWBDestinationText(
    CoordinatorEntity,
    TextEntity,
):
    """Destination text entity."""

    _attr_name = "Bestemming"
    _attr_icon = "mdi:map-marker"

    _attr_entity_category = (
        EntityCategory.CONFIG
    )

    _attr_native_min = 0
    _attr_native_max = 255

    _attr_mode = "text"

    def __init__(
        self,
        coordinator,
    ) -> None:
        """Initialize entity."""

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}"
            "_destination"
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

    @property
    def native_value(
        self,
    ) -> str:
        """Return destination."""

        return getattr(
            self.coordinator,
            "destination",
            "",
        )

    async def async_set_value(
        self,
        value: str,
    ) -> None:
        """Update destination."""

        self.coordinator.destination = (
            value.strip()
        )

        await self.coordinator.async_request_refresh()

        self.async_write_ha_state()

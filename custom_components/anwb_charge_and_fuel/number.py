"""
Number entities for ANWB Charge & Fuel.
"""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .const import (
    DEFAULT_RADIUS,
    MIN_RADIUS,
    MAX_RADIUS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        [
            ANWBRadiusNumber(coordinator),
        ]
    )


class ANWBRadiusNumber(
    CoordinatorEntity,
    NumberEntity,
):
    """Search radius."""

    _attr_name = "Zoekafstand"
    _attr_icon = "mdi:map-marker-radius"

    _attr_entity_category = EntityCategory.CONFIG

    _attr_native_min_value = MIN_RADIUS
    _attr_native_step = 1

    _attr_native_unit_of_measurement = (
        UnitOfLength.KILOMETERS
    )

    _attr_mode = "slider"

    def __init__(
        self,
        coordinator,
    ):
        """Initialize entity."""

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_radius"
        )

        if not hasattr(
            self.coordinator,
            "radius",
        ):
            self.coordinator.radius = (
                DEFAULT_RADIUS
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
    def native_value(self):
        """Return current radius."""

        return float(
            getattr(
                self.coordinator,
                "radius",
                DEFAULT_RADIUS,
            )
        )

    @property
    def native_max_value(self):
        """Return maximum allowed value."""
    
        destination = getattr(
            self.coordinator,
            "destination",
            "",
        )
    
        #
        # Geen bestemming
        #
    
        if not destination:
            return 10
    
        #
        # Bestemming aanwezig
        #
    
        route_distance = getattr(
            self.coordinator,
            "route_distance_km",
            10,
        )
    
        return max(
            1,
            int(route_distance),
        )
    
    async def async_set_native_value(
        self,
        value: float,
    ) -> None:
        """Update radius."""

        self.coordinator.radius = int(value)

        await self.coordinator.async_request_refresh()

        self.async_write_ha_state()

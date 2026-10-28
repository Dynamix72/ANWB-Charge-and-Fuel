"""
Select entities for ANWB Charge & Fuel.
"""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.helpers.device_registry import (
    DeviceInfo,
)

from homeassistant.helpers.entity import (
    EntityCategory,
)

from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from . import DOMAIN

from .const import (
    FUEL_TYPES,
    CHARGER_TYPES,
    DEFAULT_FUEL_TYPE,
    DEFAULT_CHARGER_TYPE,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""

    coordinator = hass.data[
        DOMAIN
    ][
        entry.entry_id
    ][
        "coordinator"
    ]

    data_mode = getattr(
        coordinator,
        "data_mode",
        "both",
    )

    entities = []

    if data_mode in (
        "charge",
        "both",
    ):
        entities.append(
            ANWBChargerTypeSelect(
                coordinator
            )
        )

    if data_mode in (
        "fuel",
        "both",
    ):
        entities.append(
            ANWBFuelTypeSelect(
                coordinator
            )
        )

    async_add_entities(
        entities
    )


class ANWBBaseSelect(
    CoordinatorEntity,
    SelectEntity,
):
    """Base select."""

    _attr_should_poll = False
    _attr_entity_category = (
        EntityCategory.CONFIG
    )

    def __init__(
        self,
        coordinator,
    ):
        super().__init__(coordinator)

    @property
    def current_option(
        self,
    ):
        return getattr(
            self.coordinator,
            self._coordinator_attribute,
            self.options[0],
        )

    async def async_select_option(
        self,
        option: str,
    ) -> None:
        setattr(
            self.coordinator,
            self._coordinator_attribute,
            option,
        )

        await self.coordinator.async_request_refresh()

        self.async_write_ha_state()


#
# ANWB Fuel
#


class ANWBFuelTypeSelect(
    ANWBBaseSelect,
):
    """Fuel type."""

    _attr_name = "Brandstof"

    _attr_icon = "mdi:gas-station"

    _attr_options = FUEL_TYPES

    _coordinator_attribute = "fuel_type"

    def __init__(
        self,
        coordinator,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}"
            "_fuel_type"
        )

        if not hasattr(
            coordinator,
            "fuel_type",
        ):
            coordinator.fuel_type = (
                DEFAULT_FUEL_TYPE
            )

    @property
    def device_info(
        self,
    ):
        return DeviceInfo(
            identifiers={
                (DOMAIN, "fuel")
            },
            name="ANWB Fuel",
            manufacturer="ANWB",
        )


#
# ANWB Charge
#


class ANWBChargerTypeSelect(
    ANWBBaseSelect,
):
    """Charger type."""

    _attr_name = "Laadpaaltype"

    _attr_icon = "mdi:ev-station"

    _attr_options = CHARGER_TYPES

    _coordinator_attribute = (
        "charger_type"
    )

    def __init__(
        self,
        coordinator,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}"
            "_charger_type"
        )

        if not hasattr(
            coordinator,
            "charger_type",
        ):
            coordinator.charger_type = (
                DEFAULT_CHARGER_TYPE
            )

    @property
    def device_info(
        self,
    ):
        return DeviceInfo(
            identifiers={
                (DOMAIN, "charge")
            },
            name="ANWB Charge",
            manufacturer="ANWB",
        )


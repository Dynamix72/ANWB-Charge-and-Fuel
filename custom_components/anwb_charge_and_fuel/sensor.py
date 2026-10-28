"""
Sensors exposing the cheapest chargers and fuel stations,
top-N lists and all combined results.
"""
from . import DOMAIN

from homeassistant.helpers.device_registry import (
    DeviceInfo,
)

from typing import List
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .coordinator import RouteCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
):
    """Set up ANWB sensors."""

    entry_data = hass.data.setdefault(
        "anwb_charge_and_fuel",
        {},
    ).setdefault(
        entry.entry_id,
        {},
    )

    coordinator: RouteCoordinator | None = (
        entry_data.get("coordinator")
    )

    if coordinator is None:
        raise ConfigEntryNotReady(
            "Coordinator not initialized"
        )

    entities: List[SensorEntity] = [
        ChargerCountSensor(
            coordinator,
            entry.entry_id,
        ),
        FuelCountSensor(
            coordinator,
            entry.entry_id,
        ),
        RouteMarkerSensor(
            coordinator,
            entry.entry_id,
        ),
        ANWBResultsSensor(
            coordinator,
            entry.entry_id,
        ),
    ]

    for i in range(1, 11):
        entities.append(
            TopChargerSensor(
                coordinator,
                entry.entry_id,
                i,
            )
        )

        entities.append(
            TopFuelSensor(
                coordinator,
                entry.entry_id,
                i,
            )
        )

    async_add_entities(entities)


class AnwbBaseSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """Base sensor."""

    DEVICE_TYPE = None

    def __init__(
        self,
        coordinator: RouteCoordinator,
        entry_id: str,
        name: str,
        unique_id: str,
    ):
        super().__init__(coordinator)

        self.coordinator = coordinator

        self._attr_name = name

        self._attr_unique_id = (
            f"{entry_id}_{unique_id}"
        )

    @property
    def device_info(self):
        """Return device info."""

        if self.DEVICE_TYPE == "charge":
            return DeviceInfo(
                identifiers={
                    (DOMAIN, "charge")
                },
                name="ANWB Charge",
                manufacturer="ANWB",
            )

        if self.DEVICE_TYPE == "fuel":
            return DeviceInfo(
                identifiers={
                    (DOMAIN, "fuel")
                },
                name="ANWB Fuel",
                manufacturer="ANWB",
            )

        return None


class ChargerCountSensor(
    AnwbBaseSensor,
):
    DEVICE_TYPE = "charge"
    """Number of chargers."""

    def __init__(
        self,
        coordinator,
        entry_id,
    ):
        super().__init__(
            coordinator,
            entry_id,
            "ANWB Charger Count",
            "charger_count",
        )

    @property
    def native_value(self):
        return len(
            (
                self.coordinator.data or {}
            ).get(
                "chargers",
                [],
            )
        )


class TopChargerSensor(
    AnwbBaseSensor,
):
    DEVICE_TYPE = "charge"
    """Top charger sensor."""

    def __init__(
        self,
        coordinator,
        entry_id,
        rank: int,
    ):
        super().__init__(
            coordinator,
            entry_id,
            f"ANWB Top Charger {rank}",
            f"top_charger_{rank}",
        )

        self.rank = rank

    @property
    def native_value(self):
        chargers = (
            self.coordinator.data or {}
        ).get(
            "chargers",
            [],
        )

        if len(chargers) < self.rank:
            return None

        return chargers[
            self.rank - 1
        ].get("price")

    @property
    def extra_state_attributes(self):
        chargers = (
            self.coordinator.data or {}
        ).get(
            "chargers",
            [],
        )

        if len(chargers) < self.rank:
            return {}

        item = chargers[
            self.rank - 1
        ]
        coords = (
            item.get("charger", {})
            .get("coordinates", {})
        )

        return {
            "rank": self.rank,
            "price": item.get("price"),
            "distance_km": item.get(
                "distance_km"
            ),
            "max_power_kw": item.get(
                "max_power_kw"
            ),
            "latitude": coords.get("latitude"),
            "longitude": coords.get("longitude"),
            "coordinates": coords,
            "raw": item.get("charger"),
        }


class FuelCountSensor(
    AnwbBaseSensor,
):
    DEVICE_TYPE = "fuel"
    """Fuel count."""

    def __init__(
        self,
        coordinator,
        entry_id,
    ):
        super().__init__(
            coordinator,
            entry_id,
            "ANWB Fuel Count",
            "fuel_count",
        )

    @property
    def native_value(self):
        return len(
            (
                self.coordinator.data or {}
            ).get(
                "fuel_stations",
                [],
            )
        )


class TopFuelSensor(
    AnwbBaseSensor,
):
    DEVICE_TYPE = "fuel"
    """Top fuel sensor."""

    def __init__(
        self,
        coordinator,
        entry_id,
        rank: int,
    ):
        super().__init__(
            coordinator,
            entry_id,
            f"ANWB Top Fuel {rank}",
            f"top_fuel_{rank}",
        )

        self.rank = rank

    @property
    def native_value(self):
        fuels = (
            self.coordinator.data or {}
        ).get(
            "fuel_stations",
            [],
        )

        if len(fuels) < self.rank:
            return None

        return fuels[
            self.rank - 1
        ].get("price")

    @property
    def extra_state_attributes(self):
        fuels = (
            self.coordinator.data or {}
        ).get(
            "fuel_stations",
            [],
        )

        if len(fuels) < self.rank:
            return {}

        item = fuels[
            self.rank - 1
        ]
        coords = (
            item.get("station", {})
            .get("coordinates", {})
        )

        return {
            "rank": self.rank,
            "price": item.get("price"),
            "distance_km": item.get(
                "distance_km"
            ),
            "fuel_type": item.get(
                "fuel_type"
            ),
            "latitude": coords.get("latitude"),
            "longitude": coords.get("longitude"),
            "coordinates": coords,
            "raw": item.get("station"),
        }

class RouteMarkerSensor(
    AnwbBaseSensor,
):
    """Route marker sensor."""

    DEVICE_TYPE = None

    def __init__(
        self,
        coordinator,
        entry_id,
    ):
        super().__init__(
            coordinator,
            entry_id,
            "ANWB Route Marker",
            "route_marker",
        )

    @property
    def native_value(self):
        marker = (
            self.coordinator.data or {}
        ).get(
            "route_marker"
        )

        if not marker:
            return None

        return marker.get(
            "distance_from_start"
        )

    @property
    def extra_state_attributes(self):
        marker = (
            self.coordinator.data or {}
        ).get(
            "route_marker"
        )

        if not marker:
            return {}

        return {
            "latitude": marker.get("latitude"),
            "longitude": marker.get("longitude"),
            "distance_from_start": marker.get(
                "distance_from_start"
            ),
        }


class ANWBResultsSensor(
    AnwbBaseSensor,
):
    """Combined results sensor."""

    DEVICE_TYPE = None

    def __init__(
        self,
        coordinator,
        entry_id,
    ):
        super().__init__(
            coordinator,
            entry_id,
            "ANWB Results",
            "results",
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
        """Return last update state."""

        return (
            self.coordinator.last_update_success
        )

    @property
    def extra_state_attributes(self):
        """Expose all results."""

        data = (
            self.coordinator.data or {}
        )

        return {
            "search_type": getattr(
                self.coordinator,
                "search_type",
                "fuel",
            ),
            "fuel_type": getattr(
                self.coordinator,
                "fuel_type",
                "euro95",
            ),
            "charger_type": getattr(
                self.coordinator,
                "charger_type",
                "all",
            ),
            "location_source": getattr(
                self.coordinator,
                "location_source",
                "current_location",
            ),
            "radius": getattr(
                self.coordinator,
                "radius",
                10,
            ),
            "destination": getattr(
                self.coordinator,
                "destination",
                "",
            ),
            "charger_count": len(
                data.get(
                    "chargers",
                    [],
                )
            ),
            "fuel_count": len(
                data.get(
                    "fuel_stations",
                    [],
                )
            ),
            "chargers": data.get(
                "chargers",
                [],
            ),
            "fuel_stations": data.get(
                "fuel_stations",
                [],
            ),
        }


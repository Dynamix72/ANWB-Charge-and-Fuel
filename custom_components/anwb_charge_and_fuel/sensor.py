"""
Sensors exposing the cheapest chargers and fuel stations and top-N lists.
"""

from typing import List
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import RouteCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    entry_data = hass.data.setdefault("anwb_charge_and_fuel", {}).setdefault(entry.entry_id, {})
    coordinator: RouteCoordinator | None = entry_data.get("coordinator")

    if coordinator is None:
        raise ConfigEntryNotReady("Coordinator not initialized")

    entities: List[SensorEntity] = [
        CheapestChargerSensor(coordinator, entry.entry_id),
        ChargerCountSensor(coordinator, entry.entry_id),
        CheapestFuelSensor(coordinator, entry.entry_id),
        FuelCountSensor(coordinator, entry.entry_id),
    ]

    # Top N sensors (1..5 for brevity)
    for i in range(1, 6):
        entities.append(TopChargerSensor(coordinator, entry.entry_id, i))
        entities.append(TopFuelSensor(coordinator, entry.entry_id, i))

    async_add_entities(entities)


class AnwbBaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: RouteCoordinator, entry_id: str, name: str, unique_id: str):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{unique_id}"


class CheapestChargerSensor(AnwbBaseSensor):
    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator, entry_id, "ANWB Cheapest Charger", "cheapest_charger")

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        chargers = data.get("chargers", [])
        if not chargers:
            return None
        cheapest = chargers[0]
        price = cheapest.get("price")
        return price

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        chargers = data.get("chargers", [])
        if not chargers:
            return {}
        cheapest = chargers[0]
        charger = cheapest.get("charger")
        return {
            "rank": 1,
            "price": cheapest.get("price"),
            "distance_km": cheapest.get("distance_km"),
            "max_power_kw": cheapest.get("max_power_kw"),
            "raw": charger,
        }


class ChargerCountSensor(AnwbBaseSensor):
    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator, entry_id, "ANWB Charger Count", "charger_count")

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        return len(data.get("chargers", []))


class TopChargerSensor(AnwbBaseSensor):
    def __init__(self, coordinator, entry_id: str, rank: int):
        super().__init__(coordinator, entry_id, f"ANWB Top Charger {rank}", f"top_charger_{rank}")
        self.rank = rank

    @property
    def native_value(self):
        chargers = (self.coordinator.data or {}).get("chargers", [])
        if len(chargers) < self.rank:
            return None
        item = chargers[self.rank - 1]
        return item.get("price")

    @property
    def extra_state_attributes(self):
        chargers = (self.coordinator.data or {}).get("chargers", [])
        if len(chargers) < self.rank:
            return {}
        item = chargers[self.rank - 1]
        return {
            "rank": self.rank,
            "price": item.get("price"),
            "distance_km": item.get("distance_km"),
            "max_power_kw": item.get("max_power_kw"),
            "raw": item.get("charger"),
        }


class CheapestFuelSensor(AnwbBaseSensor):
    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator, entry_id, "ANWB Cheapest Fuel", "cheapest_fuel")

    @property
    def native_value(self):
        fuels = (self.coordinator.data or {}).get("fuel_stations", [])
        if not fuels:
            return None
        return fuels[0].get("price")

    @property
    def extra_state_attributes(self):
        fuels = (self.coordinator.data or {}).get("fuel_stations", [])
        if not fuels:
            return {}
        station = fuels[0].get("station")
        return {
            "rank": 1,
            "price": fuels[0].get("price"),
            "distance_km": fuels[0].get("distance_km"),
            "raw": station,
        }


class FuelCountSensor(AnwbBaseSensor):
    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator, entry_id, "ANWB Fuel Count", "fuel_count")

    @property
    def native_value(self):
        return len((self.coordinator.data or {}).get("fuel_stations", []))


class TopFuelSensor(AnwbBaseSensor):
    def __init__(self, coordinator, entry_id: str, rank: int):
        super().__init__(coordinator, entry_id, f"ANWB Top Fuel {rank}", f"top_fuel_{rank}")
        self.rank = rank

    @property
    def native_value(self):
        fuels = (self.coordinator.data or {}).get("fuel_stations", [])
        if len(fuels) < self.rank:
            return None
        item = fuels[self.rank - 1]
        return item.get("price")

    @property
    def extra_state_attributes(self):
        fuels = (self.coordinator.data or {}).get("fuel_stations", [])
        if len(fuels) < self.rank:
            return {}
        item = fuels[self.rank - 1]
        return {
            "rank": self.rank,
            "price": item.get("price"),
            "distance_km": item.get("distance_km"),
            "raw": item.get("station"),
        }

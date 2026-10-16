"""
Sensor stubs for the integration.
"""

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class ExampleSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_name = "ANWB Example"
        self._attr_unique_id = f"{entry_id}_example"

    @property
    def native_value(self):
        return None

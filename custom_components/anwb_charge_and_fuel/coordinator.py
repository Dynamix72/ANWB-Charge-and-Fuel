"""
Coordinator skeleton for ANWB Charge & Fuel.
"""

import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)


class RouteCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, update_interval: int = 300):
        super().__init__(
            hass,
            _LOGGER,
            name="ANWB Charge & Fuel",
            update_interval=timedelta(seconds=update_interval),
        )
        self.entry = entry

    async def _async_update_data(self):
        # Implement fetching logic here
        return {}

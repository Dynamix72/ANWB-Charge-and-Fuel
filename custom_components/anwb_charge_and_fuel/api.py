"""
Minimal Route API client placeholder.
Implement real HTTP calls and parsing as needed.
"""

from typing import Any, Dict
from homeassistant.core import HomeAssistant


class RouteApi:
    def __init__(self, hass: HomeAssistant, api_key: str | None = None):
        self.hass = hass
        self.api_key = api_key

    async def get_chargers(self, lat: float, lon: float, radius_km: float) -> Dict[str, Any]:
        # Placeholder: return an empty result
        return {"value": []}

    async def get_fuel_stations(self, lat: float, lon: float, radius_km: float) -> Dict[str, Any]:
        return {"value": []}

"""
Coordinator that fetches ANWB chargers and fuel stations and exposes them to sensors.
"""

import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AnwbClient, AnwbApiError
from .const import DEFAULT_DATA_MODE

_LOGGER = logging.getLogger(__name__)


def _haversine_km(lat1, lon1, lat2, lon2):
    # Calculate the great circle distance between two points on the earth (km)
    from math import radians, sin, cos, asin, sqrt

    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6371.0 * c


def _parse_numeric_price(value):
    """Normalize various ANWB price formats into a float."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        s = value.strip().replace(" ", "")
        if not s:
            return None

        # Handle values like "1,99" or "1.234,56" or "1.99"
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")

        try:
            return float(s)
        except ValueError:
            return None

    if isinstance(value, dict):
        for key in ("price", "value"):
            parsed = _parse_numeric_price(value.get(key))
            if parsed is not None:
                return parsed
        return None

    if isinstance(value, list):
        for item in value:
            parsed = _parse_numeric_price(item)
            if parsed is not None:
                return parsed
        return None

    return None


class RouteCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry, update_interval: int = 300):
        self.hass = hass
        self.entry = entry
        self._device_tracker = entry.data.get("device_tracker")
        self._radius = entry.options.get("radius") or entry.data.get("radius") or 10
        self._ors_key = entry.options.get("ors_api_key") or entry.data.get("ors_api_key") or None
        self._client = AnwbClient(hass)

        super().__init__(
            hass,
            _LOGGER,
            name="ANWB Charge & Fuel",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        # Determine current location from the configured device_tracker entity
        tracker_state = self.hass.states.get(self._device_tracker)
        if not tracker_state:
            raise UpdateFailed(f"Device tracker {self._device_tracker} not found")

        lat = tracker_state.attributes.get("latitude")
        lon = tracker_state.attributes.get("longitude")
        if lat is None or lon is None:
            raise UpdateFailed("Device tracker does not expose latitude/longitude attributes")

        data_mode = self.entry.options.get("data_mode") or self.entry.data.get("data_mode") or DEFAULT_DATA_MODE

        result: Dict[str, Any] = {"chargers": [], "fuel_stations": [], "vehicle": {"latitude": lat, "longitude": lon}, "data_mode": data_mode}

        try:
            if data_mode in ("chargers", "both"):
                raw = await self._client.get_chargers(lat, lon, self._radius)
                items = raw.get("value", []) if isinstance(raw, dict) else []
                for item in items:
                    coords = item.get("coordinates") or {}
                    plat = coords.get("latitude")
                    plon = coords.get("longitude")
                    if plat is None or plon is None:
                        continue
                    distance_km = _haversine_km(lat, lon, plat, plon)
                    # Extract power and price if present
                    power = 0
                    evses = item.get("electricVehicleSupplyEquipment", []) or []
                    for ev in evses:
                        for conn in ev.get("connectors", []) or []:
                            try:
                                mp = float(conn.get("maxPowerInKW", 0) or 0)
                                if mp > power:
                                    power = mp
                            except Exception:
                                pass
                    price = None
                    price_field = item.get("price") or {}
                    if isinstance(price_field, dict):
                        try:
                            price = float(price_field.get("price"))
                        except Exception:
                            price = None

                    result["chargers"].append({"charger": item, "distance_km": round(distance_km, 2), "max_power_kw": power, "price": price})

            if data_mode in ("fuels", "both"):
                raw = await self._client.get_fuel_stations(lat, lon, self._radius)
                items = raw.get("value", []) if isinstance(raw, dict) else []
                for item in items:
                    coords = item.get("coordinates") or {}
                    plat = coords.get("latitude")
                    plon = coords.get("longitude")
                    if plat is None or plon is None:
                        continue
                    distance_km = _haversine_km(lat, lon, plat, plon)

                    # First: direct raw value, e.g. item["value"] = 1.899
                    price = _parse_numeric_price(item.get("value"))

                    # Fallback: common nested price structures
                    if price is None:
                        for field in ("price", "fuelPrices", "prices"):
                            v = item.get(field)
                            price = _parse_numeric_price(v)
                            if price is not None:
                                break

                    result["fuel_stations"].append({"station": item, "distance_km": round(distance_km, 2), "price": price})

        except AnwbApiError as err:
            raise UpdateFailed(f"ANWB API error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error fetching ANWB data: {err}") from err

        # Sort results for convenience
        result["chargers"].sort(key=lambda x: (x["price"] if x.get("price") is not None else float("inf"), x["distance_km"]))
        result["fuel_stations"].sort(key=lambda x: (x["price"] if x.get("price") is not None else float("inf"), x["distance_km"]))

        return result

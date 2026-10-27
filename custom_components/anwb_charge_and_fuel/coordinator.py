"""
Coordinator that fetches ANWB chargers and fuel stations
and exposes them to sensors.
"""

import logging

from datetime import timedelta
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import AnwbClient, AnwbApiError
from .const import (
    DEFAULT_FUEL_TYPE,
    DEFAULT_CHARGER_TYPE,
    DEFAULT_LOCATION_SOURCE,
    CONF_DATA_MODE,
    DEFAULT_DATA_MODE,
)


_LOGGER = logging.getLogger(__name__)


def _haversine_km(lat1, lon1, lat2, lon2):
    """Calculate distance in km."""

    from math import radians, sin, cos, asin, sqrt

    lat1, lon1, lat2, lon2 = map(
        radians,
        (lat1, lon1, lat2, lon2),
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * asin(sqrt(a))

    return 6371.0 * c


def _parse_numeric_price(value):
    """Normalize ANWB price data."""

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        s = value.strip().replace(" ", "")

        if not s:
            return None

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
            parsed = _parse_numeric_price(
                value.get(key)
            )
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
    """ANWB Route Coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry,
        update_interval: int = 300,
    ):
        self.hass = hass
        self.entry = entry
        self.config_entry = entry

        self._device_tracker = entry.data.get(
            "device_tracker"
        )

        self._ors_key = (
            entry.options.get("ors_api_key")
            or entry.data.get("ors_api_key")
            or None
        )

        self._client = AnwbClient(hass)

        #
        # Native entity settings
        #
        self.data_mode = (
            entry.options.get(CONF_DATA_MODE)
            or entry.data.get(CONF_DATA_MODE)
            or DEFAULT_DATA_MODE
        )
        self.fuel_type = "euro95"
        self.charger_type = "all"
        self.location_source = "current_location"

        #
        # Later gebruikt door number.py
        #

        self.radius = (
            entry.options.get("radius")
            or entry.data.get("radius")
            or 10
        )

        super().__init__(
            hass,
            _LOGGER,
            name="ANWB Charge & Fuel",
            update_interval=timedelta(
                seconds=update_interval
            ),
        )

    async def _async_update_data(
        self,
    ) -> Dict[str, Any]:
        """Fetch ANWB data."""

        tracker_state = self.hass.states.get(
            self._device_tracker
        )

        if not tracker_state:
            raise UpdateFailed(
                f"Device tracker {self._device_tracker} not found"
            )

        lat = tracker_state.attributes.get(
            "latitude"
        )

        lon = tracker_state.attributes.get(
            "longitude"
        )

        if lat is None or lon is None:
            raise UpdateFailed(
                "Device tracker does not expose latitude/longitude"
            )

        data_mode = self.data_mode

        result: Dict[str, Any] = {
            "chargers": [],
            "fuel_stations": [],
            "vehicle": {
                "latitude": lat,
                "longitude": lon,
            },
            "data_mode": data_mode,
        }

        try:
            #
            # CHARGERS
            #

            if data_mode in (
                "charge",
                "both",
            ):
                raw = await self._client.get_chargers(
                    lat,
                    lon,
                    self.radius,
                )

                items = (
                    raw.get("value", [])
                    if isinstance(raw, dict)
                    else []
                )

                for item in items:
                    coords = item.get(
                        "coordinates"
                    ) or {}

                    plat = coords.get(
                        "latitude"
                    )

                    plon = coords.get(
                        "longitude"
                    )

                    if (
                        plat is None
                        or plon is None
                    ):
                        continue

                    distance_km = _haversine_km(
                        lat,
                        lon,
                        plat,
                        plon,
                    )

                    power = 0

                    evses = (
                        item.get(
                            "electricVehicleSupplyEquipment",
                            [],
                        )
                        or []
                    )

                    for ev in evses:
                        for conn in ev.get(
                            "connectors",
                            [],
                        ) or []:

                            try:
                                mp = float(
                                    conn.get(
                                        "maxPowerInKW",
                                        0,
                                    )
                                    or 0
                                )

                                if mp > power:
                                    power = mp

                            except Exception:
                                pass

                    #
                    # laadpaalfilter
                    #

                    if (
                        self.charger_type
                        == "ac"
                        and power >= 50
                    ):
                        continue

                    if (
                        self.charger_type
                        == "fast"
                        and (
                            power < 50
                            or power >= 100
                        )
                    ):
                        continue

                    if (
                        self.charger_type
                        == "ultrafast"
                        and power < 100
                    ):
                        continue

                    price = None

                    price_field = (
                        item.get("price")
                        or {}
                    )

                    if isinstance(
                        price_field,
                        dict,
                    ):
                        try:
                            price = float(
                                price_field.get(
                                    "price"
                                )
                            )
                        except Exception:
                            price = None

                    result["chargers"].append(
                        {
                            "charger": item,
                            "distance_km": round(
                                distance_km,
                                2,
                            ),
                            "max_power_kw": power,
                            "price": price,
                        }
                    )

            #
            # FUEL
            #

            if data_mode in (
                "fuel",
                "both",
            ):
                raw = await self._client.get_fuel_stations(
                    lat,
                    lon,
                    self.radius,
                )

                items = (
                    raw.get("value", [])
                    if isinstance(raw, dict)
                    else []
                )

                for item in items:
                    coords = item.get(
                        "coordinates"
                    ) or {}

                    plat = coords.get(
                        "latitude"
                    )

                    plon = coords.get(
                        "longitude"
                    )

                    if (
                        plat is None
                        or plon is None
                    ):
                        continue

                    distance_km = _haversine_km(
                        lat,
                        lon,
                        plat,
                        plon,
                    )

                    price = _parse_numeric_price(
                        item.get("value")
                    )

                    if price is None:
                        for field in (
                            "price",
                            "fuelPrices",
                            "prices",
                        ):
                            v = item.get(field)

                            price = (
                                _parse_numeric_price(
                                    v
                                )
                            )

                            if (
                                price
                                is not None
                            ):
                                break

                    result[
                        "fuel_stations"
                    ].append(
                        {
                            "station": item,
                            "distance_km": round(
                                distance_km,
                                2,
                            ),
                            "price": price,
                            "fuel_type": self.fuel_type,
                        }
                    )

        except AnwbApiError as err:
            raise UpdateFailed(
                f"ANWB API error: {err}"
            ) from err

        except Exception as err:
            raise UpdateFailed(
                f"Unexpected error fetching ANWB data: {err}"
            ) from err

        result["chargers"].sort(
            key=lambda x: (
                x["price"]
                if x.get("price")
                is not None
                else float("inf"),
                x["distance_km"],
            )
        )

        result["fuel_stations"].sort(
            key=lambda x: (
                x["price"]
                if x.get("price")
                is not None
                else float("inf"),
                x["distance_km"],
            )
        )

        return result

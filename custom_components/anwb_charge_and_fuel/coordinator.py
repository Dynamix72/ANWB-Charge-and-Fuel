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

""""
The default search radius is 10 km because otherwise the ANWB API returns too many results, causing it to return no data at all.
"""
DEFAULT_SEARCH_RADIUS_KM = 10

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


def _normalize_fuel_type(value):
    """Normalize ANWB fuel-type values to the integration format."""

    if value is None:
        return None

    if isinstance(value, (list, tuple, set)):
        for item in value:
            normalized = _normalize_fuel_type(item)
            if normalized is not None:
                return normalized
        return None

    text = str(value).strip().lower()
    text = "".join(ch for ch in text if ch.isalnum())

    if not text:
        return None

    if text.startswith("euro95") or "euro95" in text:
        return "euro95"

    if (
        text.startswith("euro98")
        or "superplus" in text
        or text.startswith("super98")
        or text.startswith("superplus98")
        or "super98" in text
    ):
        return "superplus"

    if (
        text.startswith("diesel")
        or text.startswith("b7")
        or text.startswith("b10")
        or "diesel" in text
    ):
        return "diesel"

    if (
        text.startswith("lpg")
        or text.startswith("autogas")
        or text.startswith("cng")
        or "autogas" in text
        or "cng" in text
    ):
        return "lpg"

    return text


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


def _connector_matches_charger_type(power_kw: float, charger_type: str) -> bool:
    """Return True when connector power matches the selected charger type."""

    if not charger_type or charger_type == "all":
        return True

    if charger_type == "ac":
        return power_kw < 50

    if charger_type == "fast":
        return 50 <= power_kw < 100

    if charger_type == "ultrafast":
        return power_kw >= 100

    return True


def _get_connector_power_kw(connector: dict) -> float:
    """Return connector power in kW."""

    if not isinstance(connector, dict):
        return 0.0

    value = connector.get("maxPowerInKW")

    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _extract_connector_price(connector: dict):
    """Extract the energy price from a connector, preferring ENERGY components."""

    if not isinstance(connector, dict):
        return None

    prices = connector.get("prices")
    if isinstance(prices, dict):
        prices = [prices]

    if isinstance(prices, list):
        for price_entry in prices:
            if not isinstance(price_entry, dict):
                continue

            price_components = (
                price_entry.get("priceComponents") or []
            )

            if isinstance(price_components, list):
                for component in price_components:
                    if not isinstance(component, dict):
                        continue

                    code = str(component.get("code") or "").upper()
                    name = str(component.get("name") or "").lower()

                    if code == "ENERGY" or name == "energie":
                        parsed = _parse_numeric_price(
                            component.get("value")
                        )
                        if parsed is not None:
                            return parsed

            parsed = _parse_numeric_price(
                price_entry.get("value")
                or price_entry.get("price")
            )
            if parsed is not None:
                return parsed

    parsed = _parse_numeric_price(connector.get("price"))
    if parsed is not None:
        return parsed

    return None


def _extract_charger_price(item: dict, charger_type: str):
    """Return the most relevant charger price for the selected charger type."""

    if not isinstance(item, dict):
        return None

    evses = item.get("electricVehicleSupplyEquipment", []) or []
    connectors = []

    for evse in evses:
        if not isinstance(evse, dict):
            continue

        for connector in evse.get("connectors", []) or []:
            if isinstance(connector, dict):
                connectors.append(connector)

    if not connectors:
        return _parse_numeric_price(item.get("price"))

    if charger_type in ("ac", "fast", "ultrafast"):
        matched_connectors = [
            connector
            for connector in connectors
            if _connector_matches_charger_type(
                _get_connector_power_kw(connector),
                charger_type,
            )
        ]
        connectors = matched_connectors or connectors

    for connector in connectors:
        price = _extract_connector_price(connector)
        if price is not None:
            return price

    return _parse_numeric_price(item.get("price"))


def _extract_fuel_station_details(item, selected_fuel_type):
    """Extract the matching fuel type and price from a station payload."""

    selected = _normalize_fuel_type(selected_fuel_type) or "euro95"

    fuel_type = _normalize_fuel_type(
        item.get("fullType")
        or item.get("fuelType")
        or item.get("fuel_type")
        or item.get("type")
    )

    if fuel_type is None:
        fuel_type = selected

    price_candidates = []

    for field in ("prices", "fuelPrices"):
        value = item.get(field)
        if isinstance(value, list):
            price_candidates.extend(value)
        elif isinstance(value, dict):
            price_candidates.append(value)

    for entry in price_candidates:
        if not isinstance(entry, dict):
            continue

        entry_type = _normalize_fuel_type(
            entry.get("fuelType")
            or entry.get("fullType")
            or entry.get("fuelTypeCode")
            or entry.get("fuelName")
            or entry.get("name")
            or entry.get("type")
        )

        if entry_type is None:
            continue

        if entry_type != selected:
            continue

        parsed = _parse_numeric_price(
            entry.get("value")
            or entry.get("price")
        )

        if parsed is not None:
            return entry_type, parsed

    candidate_price = _parse_numeric_price(item.get("value"))

    if candidate_price is None:
        for field in ("price", "fuelPrices", "prices"):
            value = item.get(field)
            if isinstance(value, dict):
                for key, subvalue in value.items():
                    key_type = _normalize_fuel_type(key)
                    if key_type is None:
                        continue

                    if key_type != selected and fuel_type != selected:
                        continue

                    parsed = _parse_numeric_price(subvalue)
                    if parsed is not None:
                        fuel_type = key_type
                        candidate_price = parsed
                        break

                if candidate_price is not None:
                    break

            parsed = _parse_numeric_price(value)
            if parsed is not None:
                candidate_price = parsed
                break

    if candidate_price is None and isinstance(item.get("fuelPrices"), list):
        for entry in item.get("fuelPrices") or []:
            if not isinstance(entry, dict):
                continue

            entry_type = _normalize_fuel_type(
                entry.get("fullType")
                or entry.get("fuelType")
                or entry.get("fuel_type")
                or entry.get("name")
            )

            if entry_type is not None and selected and entry_type != selected:
                continue

            parsed = _parse_numeric_price(
                entry.get("price")
                or entry.get("value")
            )
            if parsed is not None:
                fuel_type = entry_type or fuel_type
                candidate_price = parsed
                break

    if candidate_price is None:
        candidate_price = _parse_numeric_price(item.get("price"))

    return fuel_type, candidate_price


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
        self.fuel_type = DEFAULT_FUEL_TYPE
        self.charger_type = DEFAULT_CHARGER_TYPE
        self.location_source = DEFAULT_LOCATION_SOURCE

        #
        # Later gebruikt door number.py
        #

        self.radius = (
            entry.options.get("radius")
            or entry.data.get("radius")
            or 10
        )
        
        #
        # Route informatie
        #
        
        self.route_distance_km = 10
        
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
        
        search_lat = lat
        search_lon = lon
        search_radius = min(self.radius, 10)        
        
        destination = getattr(
            self,
            "destination",
            "",
        )
        
        route_marker = None
        
        if destination and self._ors_key:
        
            try:

                destination_data = (
                    await self._client.geocode_destination(
                        self._ors_key,
                        destination,
                    )
                )
          
                route = await self._client.get_route(
                    self._ors_key,
                    lat,
                    lon,
                    destination_data["latitude"],
                    destination_data["longitude"],
                )
        
                self.route_distance_km = (
                    route["distance_km"]
                )
       
                marker = (
                    self._client.get_marker_on_route(
                        route["geometry"],
                        min(
                            self.radius,
                            route["distance_km"],
                        ),
                    )
                )
                
                route_marker = marker
                
                _LOGGER.warning(
                    "ANWB MARKER=%s",
                    marker,
                )
                
 
                search_lat = lat
                search_lon = lon
                search_radius = min(self.radius, 10)
                
                if marker:
                    search_lat = marker["latitude"]
                    search_lon = marker["longitude"]
                    search_radius = self.radius
                
                _LOGGER.warning(
                    "ANWB SEARCH CENTER=%s,%s radius=%s",
                    search_lat,
                    search_lon,
                    search_radius,
                )
            
            except Exception as err:
        
                _LOGGER.error(
                    "ANWB ORS ERROR: %s",
                    err,
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
            "route_marker": route_marker,
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
                    search_lat,
                    search_lon,
                    search_radius,
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

                    price = _extract_charger_price(
                        item,
                        self.charger_type,
                    )

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
                    search_lat,
                    search_lon,
                    search_radius,
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

                    fuel_type, price = _extract_fuel_station_details(
                        item,
                        self.fuel_type,
                    )

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
                            "fuel_type": fuel_type,
                            "fulltype": fuel_type,
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

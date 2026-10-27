"""
ANWB API client.

Fetches chargers and fuel stations from the ANWB
Points Of Interest API.

The client intentionally returns raw ANWB JSON.
Filtering is performed in the coordinator.
"""

from __future__ import annotations

import asyncio
import logging
import math

from typing import Any

import aiohttp

from aiohttp.client_exceptions import ClientError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)

_LOGGER = logging.getLogger(__name__)

ANWB_BASE = (
    "https://api.anwb.nl/"
    "routing/points-of-interest/v3/all"
)

ORS_GEOCODE_URL = (
    "https://api.heigit.org/pelias/v1/search"
)

ORS_ROUTE_URL = (
    "https://api.heigit.org/openrouteservice/v2/directions/driving-car/geojson"
)

class AnwbApiError(Exception):
    """ANWB API exception."""


class AnwbClient:
    """ANWB API client."""

    def __init__(
        self,
        hass: HomeAssistant,
        timeout: float = 10.0,
    ) -> None:
        self.hass = hass
        self._session = async_get_clientsession(
            hass
        )
        self._timeout = timeout

    async def _get(
        self,
        params: dict[str, Any],
        retries: int = 2,
    ) -> dict[str, Any]:
        """Execute GET request."""

        attempt = 0
        backoff = 1.0

        while True:
            attempt += 1

            try:
                timeout = aiohttp.ClientTimeout(
                    total=self._timeout
                )

                async with self._session.get(
                    ANWB_BASE,
                    params=params,
                    timeout=timeout,
                ) as resp:

                    status = resp.status
                    text = await resp.text()

                    _LOGGER.debug(
                        "ANWB HTTP %s %s...",
                        status,
                        text[:200],
                    )

                    #
                    # Rate limiting
                    #

                    if (
                        status == 429
                        and attempt <= retries
                    ):
                        _LOGGER.info(
                            "ANWB rate limited "
                            "retry %s/%s",
                            attempt,
                            retries,
                        )

                        await asyncio.sleep(
                            backoff
                        )

                        backoff *= 2

                        continue

                    #
                    # Server errors
                    #

                    if (
                        500 <= status < 600
                        and attempt <= retries
                    ):
                        _LOGGER.info(
                            "ANWB server error %s "
                            "retry %s/%s",
                            status,
                            attempt,
                            retries,
                        )

                        await asyncio.sleep(
                            backoff
                        )

                        backoff *= 2

                        continue

                    if status < 200 or status >= 300:
                        raise AnwbApiError(
                            f"ANWB HTTP error "
                            f"{status}: "
                            f"{text[:200]}"
                        )

                    try:
                        return await resp.json()

                    except Exception as err:
                        raise AnwbApiError(
                            "Failed to parse "
                            f"ANWB JSON: {err}"
                        ) from err

            except (
                ClientError,
                asyncio.TimeoutError,
            ) as err:

                _LOGGER.debug(
                    "Network error calling ANWB: %s",
                    err,
                )

                if attempt <= retries:
                    await asyncio.sleep(backoff)

                    backoff *= 2

                    continue

                raise AnwbApiError(
                    f"Network error: {err}"
                ) from err

    async def _ors_get(
        self,
        url: str,
        api_key: str,
        params: dict,
    ) -> dict:
        """Execute ORS GET request."""
    
        timeout = aiohttp.ClientTimeout(
            total=self._timeout
        )
    
        headers = {
            "Authorization": api_key,
        }
    
        async with self._session.get(
            url,
            headers=headers,
            params=params,
            timeout=timeout,
        ) as resp:
    
            if resp.status != 200:
                raise AnwbApiError(
                    f"ORS error {resp.status}"
                )
    
            return await resp.json()

    async def geocode_destination(
        self,
        api_key: str,
        destination: str,
    ) -> dict:
        """Convert address to coordinates."""
    
        result = await self._ors_get(
            ORS_GEOCODE_URL,
            api_key,
            {
                "text": destination,
                "size": 1,
            },
        )
    
        features = result.get(
            "features",
            [],
        )
    
        if not features:
            raise AnwbApiError(
                f"Destination not found: {destination}"
            )
    
        coords = (
            features[0]
            ["geometry"]
            ["coordinates"]
        )
    
        return {
            "longitude": coords[0],
            "latitude": coords[1],
            "label": features[0]
            ["properties"]
            .get(
                "label",
                destination,
            ),
        }
    
    async def get_chargers(
        self,
        lat: float,
        lon: float,
        radius_km: float,
    ) -> dict[str, Any]:
        """Return charging locations."""

        params = {
            "bounding-box-filter":
                self._compute_bbox(
                    lat,
                    lon,
                    radius_km,
                ),
            "type-filter":
                "CHARGING_LOCATION",
        }

        return await self._get(params)

    async def get_fuel_stations(
        self,
        lat: float,
        lon: float,
        radius_km: float,
    ) -> dict[str, Any]:
        """Return fuel stations."""

        params = {
            "bounding-box-filter":
                self._compute_bbox(
                    lat,
                    lon,
                    radius_km,
                ),
            "type-filter":
                "FUEL_STATION",
        }

        return await self._get(params)

    async def get_route(
        self,
        api_key: str,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
    ) -> dict:
        """Get route from ORS."""
    
        timeout = aiohttp.ClientTimeout(
            total=self._timeout
        )
    
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
    
        payload = {
            "coordinates": [
                [start_lon, start_lat],
                [end_lon, end_lat],
            ]
        }
    
        async with self._session.post(
            ORS_ROUTE_URL,
            headers=headers,
            json=payload,
            timeout=timeout,
        ) as resp:
    
            if resp.status != 200:
                raise AnwbApiError(
                    f"ORS route error {resp.status}"
                )
    
            result = await resp.json()
    
        feature = result["features"][0]
    
        summary = (
            feature["properties"]
            ["summary"]
        )
    
        return {
            "distance_km":
                round(
                    summary["distance"]
                    / 1000,
                    1,
                ),
            "duration_min":
                round(
                    summary["duration"]
                    / 60,
                    1,
                ),
            "geometry":
                feature["geometry"],
        }    
    
    def get_marker_on_route(
        self,
        route_geometry: dict,
        distance_km: float,
    ) -> dict:
        """Return point on route."""
    
        coords = (
            route_geometry["coordinates"]
        )
    
        target_meters = (
            distance_km * 1000
        )
    
        travelled = 0
    
        for i in range(
            len(coords) - 1
        ):
    
            lon1, lat1 = coords[i]
            lon2, lat2 = coords[i + 1]
    
            dx = lon2 - lon1
            dy = lat2 - lat1
    
            segment_length = (
                math.sqrt(
                    dx * dx +
                    dy * dy
                )
                * 111000
            )
    
            if (
                travelled
                + segment_length
                >= target_meters
            ):
    
                remaining = (
                    target_meters
                    - travelled
                )
    
                ratio = (
                    remaining
                    / segment_length
                )
    
                marker_lon = (
                    lon1 +
                    (
                        (lon2 - lon1)
                        * ratio
                    )
                )
    
                marker_lat = (
                    lat1 +
                    (
                        (lat2 - lat1)
                        * ratio
                    )
                )
    
                return {
                    "latitude": marker_lat,
                    "longitude": marker_lon,
                    "distance_from_start":
                        distance_km,
                }
    
            travelled += segment_length
    
        last_lon, last_lat = (
            coords[-1]
        )
    
        return {
            "latitude": last_lat,
            "longitude": last_lon,
            "distance_from_start":
                distance_km,
        }    
        
    async def get_chargers_for_destination(
        self,
        lat: float,
        lon: float,
        radius_km: float,
    ) -> dict[str, Any]:
        """Future use for destination search."""

        return await self.get_chargers(
            lat,
            lon,
            radius_km,
        )

    async def get_fuels_for_destination(
        self,
        lat: float,
        lon: float,
        radius_km: float,
    ) -> dict[str, Any]:
        """Future use for destination search."""

        return await self.get_fuel_stations(
            lat,
            lon,
            radius_km,
        )

    @staticmethod
    def _compute_bbox(
        lat: float,
        lon: float,
        radius_km: float,
    ) -> str:
        """Create bounding box."""

        lat_delta = radius_km / 111.0

        cos_lat = math.cos(
            math.radians(lat)
        )

        if abs(cos_lat) < 0.0001:
            cos_lat = 0.0001

        lon_delta = (
            radius_km
            / (111.0 * abs(cos_lat))
        )

        min_lat = lat - lat_delta
        min_lon = lon - lon_delta
        max_lat = lat + lat_delta
        max_lon = lon + lon_delta

        return (
            f"{min_lat},"
            f"{min_lon},"
            f"{max_lat},"
            f"{max_lon}"
        )

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

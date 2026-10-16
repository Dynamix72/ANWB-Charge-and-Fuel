"""
Lightweight ANWB POI API client.
Uses Home Assistant's async_get_clientsession to perform requests to the ANWB POI endpoint.
This client intentionally keeps logic small: it returns the raw JSON from the ANWB POI endpoint
and handles simple retries for 429/5xx responses.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp
from aiohttp import ClientResponse
from aiohttp.client_exceptions import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

ANWB_BASE = "https://api.anwb.nl/routing/points-of-interest/v3/all"


class AnwbApiError(Exception):
    pass


class AnwbClient:
    def __init__(self, hass: HomeAssistant, timeout: float = 10.0):
        self.hass = hass
        self._session = async_get_clientsession(hass)
        self._timeout = timeout

    async def _get(self, params: Dict[str, Any], retries: int = 2) -> Dict[str, Any]:
        attempt = 0
        backoff = 1.0
        while True:
            attempt += 1
            try:
                timeout = aiohttp.ClientTimeout(total=self._timeout)
                async with self._session.get(ANWB_BASE, params=params, timeout=timeout) as resp:
                    status = resp.status
                    text = await resp.text()
                    _LOGGER.debug("ANWB HTTP %s %s...", status, text[:200])

                    if status == 429 and attempt <= retries:
                        _LOGGER.info("ANWB rate limited, retry %d/%d", attempt, retries)
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue

                    if 500 <= status < 600 and attempt <= retries:
                        _LOGGER.info("ANWB server error %s, retry %d/%d", status, attempt, retries)
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue

                    if status < 200 or status >= 300:
                        raise AnwbApiError(f"ANWB HTTP error {status}: {text[:200]}")

                    try:
                        return await resp.json()
                    except Exception as err:
                        raise AnwbApiError(f"Failed to parse JSON from ANWB: {err}") from err

            except (ClientError, asyncio.TimeoutError) as err:
                _LOGGER.debug("Network error when calling ANWB: %s", err)
                if attempt <= retries:
                    _LOGGER.info("Network error; retry %d/%d", attempt, retries)
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise AnwbApiError(f"Network error when calling ANWB: {err}") from err

    async def get_chargers(self, lat: float, lon: float, radius_km: float) -> Dict[str, Any]:
        bbox = self._compute_bbox(lat, lon, radius_km)
        params = {"bounding-box-filter": bbox, "type-filter": "CHARGING_LOCATION"}
        return await self._get(params)

    async def get_fuel_stations(self, lat: float, lon: float, radius_km: float) -> Dict[str, Any]:
        bbox = self._compute_bbox(lat, lon, radius_km)
        params = {"bounding-box-filter": bbox, "type-filter": "FUEL_STATION"}
        return await self._get(params)

    @staticmethod
    def _compute_bbox(lat: float, lon: float, radius_km: float) -> str:
        # Simple equirectangular bbox approximation
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * abs(__import__("math").cos(__import__("math").radians(lat))) if abs(__import__("math").cos(__import__("math").radians(lat))) > 0 else 1.0)
        return f"{lat - lat_delta},{lon - lon_delta},{lat + lat_delta},{lon + lon_delta}"

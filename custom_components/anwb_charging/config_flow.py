"""
Configuration Flow voor ANWB Fuel & Charging Integration.
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    DOMAIN,
    CONF_DEVICE_TRACKER,
    CONF_ORS_API_KEY,
    CONF_DATA_MODE,
    CONF_FUEL_TYPE,
    DEFAULT_DATA_MODE,
    DEFAULT_FUEL_TYPE,
    DATA_MODES,
    FUEL_TYPES,
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Initiële setup flow voor ANWB Fuel & Charging integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle initiële configuratie."""

        if user_input is not None:
            await self.async_set_unique_id(
                user_input[CONF_DEVICE_TRACKER]
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="ANWB Fuel & Charging",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE_TRACKER
                    ): EntitySelector(
                        EntitySelectorConfig(
                            domain="device_tracker"
                        )
                    ),
                    vol.Optional(
                        CONF_DATA_MODE,
                        default=DEFAULT_DATA_MODE,
                    ): SelectSelector(
                        SelectSelectorConfig(
{
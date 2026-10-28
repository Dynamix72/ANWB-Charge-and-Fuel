"""
Config flow for ANWB Charge & Fuel.
"""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components import persistent_notification

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
    DATA_MODES,
    DEFAULT_DATA_MODE,
)


class ConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input=None,
    ):
        """Handle initial setup."""
        if user_input is not None:
        
            old_data_mode = (
                self._config_entry.options.get(
                    CONF_DATA_MODE
                )
                or self._config_entry.data.get(
                    CONF_DATA_MODE
                )
                or DEFAULT_DATA_MODE
            )
        
            new_data_mode = user_input.get(
                CONF_DATA_MODE,
                DEFAULT_DATA_MODE,
            )
        
            self.hass.config_entries.async_update_entry(
                self._config_entry,
                options={
                    CONF_DEVICE_TRACKER:
                        user_input.get(
                            CONF_DEVICE_TRACKER
                        ),
                    CONF_DATA_MODE:
                        new_data_mode,
                    CONF_ORS_API_KEY:
                        user_input.get(
                            CONF_ORS_API_KEY,
                            "",
                        ),
                },
            )
        
            if old_data_mode != new_data_mode:
                persistent_notification.create(
                    self.hass,
                    (
                        "De ANWB Charge & Fuel modus is gewijzigd.\n\n"
                        "Herstart Home Assistant om alle "
                        "Charge/Fuel entities correct aan te "
                        "maken of te verwijderen."
                    ),
                    title="ANWB Charge & Fuel",
                    notification_id=(
                        "anwb_restart_required"
                    ),
                )
        
            return self.async_create_entry(
                title="",
                data={},
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
                            options=DATA_MODES,
                            mode="dropdown",
                        )
                    ),

                    vol.Optional(
                        CONF_ORS_API_KEY,
                        default="",
                    ): TextSelector(
                        TextSelectorConfig(
                            multiline=False,
                        )
                    ),
                }
            ),
        )

    @staticmethod
    def async_get_options_flow(
        config_entry,
    ):
        """Return options flow."""

        return OptionsFlowHandler(
            config_entry
        )


class OptionsFlowHandler(
    config_entries.OptionsFlow,
):
    """Handle options."""

    def __init__(
        self,
        config_entry,
    ):
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input=None,
    ):
        """Manage options."""

        if user_input is not None:

            self.hass.config_entries.async_update_entry(
                self._config_entry,
                options={
                    CONF_DEVICE_TRACKER:
                        user_input.get(
                            CONF_DEVICE_TRACKER
                        ),

                    CONF_DATA_MODE:
                        user_input.get(
                            CONF_DATA_MODE,
                            DEFAULT_DATA_MODE,
                        ),

                    CONF_ORS_API_KEY:
                        user_input.get(
                            CONF_ORS_API_KEY,
                            "",
                        ),
                },
            )

            return self.async_create_entry(
                title="",
                data={},
            )

        current_tracker = (
            self._config_entry.options.get(
                CONF_DEVICE_TRACKER
            )
            or self._config_entry.data.get(
                CONF_DEVICE_TRACKER
            )
        )

        current_data_mode = (
            self._config_entry.options.get(
                CONF_DATA_MODE
            )
            or self._config_entry.data.get(
                CONF_DATA_MODE
            )
            or DEFAULT_DATA_MODE
        )

        current_ors_key = (
            self._config_entry.options.get(
                CONF_ORS_API_KEY
            )
            or self._config_entry.data.get(
                CONF_ORS_API_KEY
            )
            or ""
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE_TRACKER,
                        default=current_tracker,
                    ): EntitySelector(
                        EntitySelectorConfig(
                            domain="device_tracker"
                        )
                    ),

                    vol.Required(
                        CONF_DATA_MODE,
                        default=current_data_mode,
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=DATA_MODES,
                            mode="dropdown",
                        )
                    ),

                    vol.Optional(
                        CONF_ORS_API_KEY,
                        default=current_ors_key,
                    ): TextSelector(
                        TextSelectorConfig(
                            multiline=False,
                        )
                    ),
                }
            ),
        )

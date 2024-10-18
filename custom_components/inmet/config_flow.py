"""Config flow to configure the GDACS integration."""

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_CODE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
)
from homeassistant.helpers import config_validation as cv

from .const import DEFAULT_CODE, DEFAULT_SCAN_INTERVAL, DOMAIN

DATA_SCHEMA = vol.Schema(
    {vol.Optional(CONF_CODE, default=DEFAULT_CODE): cv.positive_int}
)

_LOGGER = logging.getLogger(__name__)


class InmetFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a InMet config flow."""

    async def _show_form(
        self, errors: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Show the form to the user."""
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors or {}
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the start of the config flow."""
        _LOGGER.debug("User input: %s", user_input)
        if not user_input:
            return await self._show_form()

        city_code = user_input.get(CONF_CODE, DEFAULT_CODE)
        user_input[CONF_CODE] = city_code

        details = await self._fetch_city_details(city_code)
        if details is None:
            return await self._show_form(errors={"base": "cannot_connect"})

        detail = details[0]
        user_input[CONF_LATITUDE] = detail["latitude"]
        user_input[CONF_LONGITUDE] = detail["longitude"]
        user_input[CONF_NAME] = detail["label"]

        identifier = f"inmet_{user_input[CONF_CODE]}"
        title = f"InMet Alert {user_input[CONF_NAME]}"

        await self.async_set_unique_id(identifier)
        self._abort_if_unique_id_configured()

        scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        user_input[CONF_SCAN_INTERVAL] = scan_interval.total_seconds()

        return self.async_create_entry(title=title, data=user_input)

    async def _fetch_city_details(self, city_code: str) -> dict | None:
        """Fetch city details from external server."""
        url = f"https://apiprevmet3.inmet.gov.br/buscar/cidade/{city_code}"
        try:
            async with aiohttp.ClientSession() as session, session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to fetch details for city code: %s", city_code
                    )
                    return None
                return await response.json()
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching city details: %s", err)
            return None

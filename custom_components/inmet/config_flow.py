"""Config flow to configure the InMet integration."""

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

from .const import DEFAULT_NAME, DEFAULT_SCAN_INTERVAL, DOMAIN, MAX_CITIES

DATA_SCHEMA = vol.Schema({vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string})

_LOGGER = logging.getLogger(__name__)


class InmetFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a InMet config flow."""

    cities = []

    async def _show_form(
        self,
        step_id: str,
        data_schema: vol.Schema,
        errors: dict[str, str] | None = None,
    ) -> ConfigFlowResult:
        """Show a form to the user."""
        return self.async_show_form(
            step_id=step_id, data_schema=data_schema, errors=errors or {}
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the start of the config flow."""
        _LOGGER.debug("User input: %s", user_input)
        if not user_input:
            return await self._show_form("user", DATA_SCHEMA)

        city_name = user_input.get(CONF_NAME, DEFAULT_NAME)

        # Realiza a busca da cidade e limita o número de resultados ao valor de MAX_CITIES
        all_cities = await self._search_city(city_name)
        if all_cities is None:
            return await self._show_form(
                "user", DATA_SCHEMA, errors={"base": "cannot_connect"}
            )

        # Limitar a lista de cidades ao número definido em MAX_CITIES
        self.cities = all_cities[:MAX_CITIES]

        if len(self.cities) == 1:
            return await self._create_entry_from_city(self.cities[0])

        # Se houver múltiplas cidades, pedir ao usuário para escolher uma
        city_names = {
            city["geocode"]: f"{city['label']} ({city['geocode']})"
            for city in self.cities
        }

        # Adicionar uma opção extra para voltar, usando o texto de tradução diretamente
        city_names["back"] = "Voltar para digitar outro nome de cidade"

        # Use vol.Optional para exibir como radio buttons
        city_selection_schema = vol.Schema(
            {vol.Optional("city_code"): vol.In(city_names)}
        )

        return await self._show_form("select_city", city_selection_schema)

    async def async_step_select_city(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle city selection step."""
        city_code = user_input["city_code"]

        # Verifique se o usuário escolheu "Voltar"
        if city_code == "back":
            return await self.async_step_user()

        # Encontre a cidade com o código selecionado
        city = next(
            (city for city in self.cities if city["geocode"] == city_code), None
        )

        if not city:
            return await self._show_form(
                "select_city",
                vol.Schema(
                    {
                        vol.Optional("city_code"): vol.In(
                            {
                                c["geocode"]: f"{c['label']} ({c['geocode']})"
                                for c in self.cities
                            }
                        )
                    }
                ),
                errors={"base": "city_not_found"},
            )

        # Crie a entrada de configuração a partir da cidade selecionada
        return await self._create_entry_from_city(city)

    async def _create_entry_from_city(self, city: dict) -> ConfigFlowResult:
        """Create config entry from city data."""
        user_input = {
            CONF_CODE: city["geocode"],
            CONF_LATITUDE: city["latitude"],
            CONF_LONGITUDE: city["longitude"],
            CONF_NAME: city["label"],
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL.total_seconds(),
        }

        identifier = f"inmet_{user_input[CONF_CODE]}"
        title = f"InMet Alert {user_input[CONF_NAME]}"

        await self.async_set_unique_id(identifier)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=title, data=user_input)

    async def _search_city(self, name: str) -> list | None:
        """Search the city using the inmet endpoint."""
        url = f"https://apiprevmet3.inmet.gov.br/autocomplete/{name}"
        try:
            async with aiohttp.ClientSession() as session, session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to search city: %s", name)
                    return None
                return await response.json()
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching city details: %s", err)
            return None

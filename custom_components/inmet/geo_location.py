"""Geolocation support for GDACS Feed."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import logging
import math
from typing import Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from . import InMetEntityManager
from .const import ALERT_ICON, DOMAIN, FEED

_LOGGER = logging.getLogger(__name__)

ATTR_ALERT_DESCRIPTION = "description"
ATTR_ALERT_ID = "alert_id"
ATTR_ALERT_SEVERITY = "severity"
ATTR_ALERT_SEVERITY_ID = "severity_id"
ATTR_ALERT_RISKS = "risks"
ATTR_ALERT_INSTRUCTIONS = "instructions"
ATTR_ALERT_COLOR = "color"
ATTR_ALERT_UPDATED = "updated"
ATTR_ALERT_FINISHED = "finished"
ATTR_ALERT_START_DATE = "start_date"
ATTR_ALERT_END_DATE = "end_date"
ATTR_ALERT_SEQUENCE = "sequence"
ATTR_ALERT_FUTURE = "future"
ATTR_ALERT_URL = "url"

DATE_FORMAT = "%Y-%m-%d %H:%M"


ICONS = {
    "Chuvas Intensas": "mdi:weather-lightning",
    "Tempestade": "mdi:weather-lightning-rainy",
    "Acumulado de Chuva": "mdi:home-flood",
    "Onda de Calor": "mdi:heat-wave",
}

# An update of this entity is not making a web request, but uses internal data only.
PARALLEL_UPDATES = 0

SOURCE = "inmet"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the InMet Feed platform."""
    manager: InMetEntityManager = hass.data[DOMAIN][FEED][entry.entry_id]

    @callback
    def async_add_geolocation(
        feed_manager: InMetEntityManager, integration_id: str, external_id: str
    ) -> None:
        """Add geolocation entity from feed."""
        new_entity = InmetEvent(feed_manager, integration_id, external_id)
        _LOGGER.debug("Adding geolocation %s", new_entity)
        async_add_entities([new_entity], True)

    manager.listeners.append(
        async_dispatcher_connect(
            hass, manager.async_event_new_entity(), async_add_geolocation
        )
    )
    # Do not wait for update here so that the setup can be completed and because an
    # update will fetch data from the feed via HTTP and then process that data.
    hass.async_create_task(manager.async_update())
    _LOGGER.debug("Geolocation setup done")


class InmetEvent(GeolocationEvent):
    """Represents an external event with GDACS feed data."""

    _attr_should_poll = False
    _attr_source = SOURCE

    def __init__(
        self,
        feed_manager: InMetEntityManager,
        integration_id: str,
        alert_id: str,
    ) -> None:
        """Initialize entity with data from feed entry."""
        self._feed_manager = feed_manager
        self._alert_id = alert_id
        self._attr_unique_id = f"{integration_id}_{alert_id}"
        self._attr_unit_of_measurement = UnitOfLength.KILOMETERS

        self._description: str | None = None
        self._alert_severity: str | None = None
        self._alert_severity_id: int | None = None
        self._alert_risks: str | None = None
        self._alert_instructions: str | None = None
        self._alert_color: str | None = None
        self._alert_updated: bool | None = None
        self._alert_finished: bool | None = None
        self._alert_future: bool | None = None
        self._alert_start_date: datetime | None = None
        self._alert_end_date: datetime | None = None
        self._alert_sequence: int | None = None
        self._alert_url: str | None = None

        self._version: int | None = None
        self._remove_signal_delete: Callable[[], None]
        self._remove_signal_update: Callable[[], None]

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        if self.hass.config.units is US_CUSTOMARY_SYSTEM:
            self._attr_unit_of_measurement = UnitOfLength.MILES
        self._remove_signal_delete = async_dispatcher_connect(
            self.hass, f"inmet_delete_{self._alert_id}", self._delete_callback
        )
        self._remove_signal_update = async_dispatcher_connect(
            self.hass, f"inmet_update_{self._alert_id}", self._update_callback
        )

    async def async_will_remove_from_hass(self) -> None:
        """Call when entity will be removed from hass."""
        self._remove_signal_delete()
        self._remove_signal_update()
        # Remove from entity registry.
        entity_registry = er.async_get(self.hass)
        if self.entity_id in entity_registry.entities:
            entity_registry.async_remove(self.entity_id)

    @callback
    def _delete_callback(self) -> None:
        """Remove this entity."""
        self.hass.async_create_task(self.async_remove(force_remove=True))

    @callback
    def _update_callback(self) -> None:
        """Call update method."""
        self.async_schedule_update_ha_state(True)

    async def async_update(self) -> None:
        """Update this entity from the data held in the feed manager."""
        _LOGGER.debug("Updating %s", self._alert_id)
        alert = self._feed_manager.get_entry(self._alert_id)
        if alert:
            self._update_from_feed(alert)

    def _update_from_feed(self, alert: dict) -> None:
        """Update the internal state from the provided feed entry."""
        self._description = alert["descricao"]
        self._attr_latitude = self._feed_manager.latitude()
        self._attr_longitude = self._feed_manager.longitude()

        self._attr_distance = self._haversine()

        self._alert_severity = alert["severidade"]
        self._alert_severity_id = alert["id_severidade"]
        self._alert_risks = alert["riscos"]
        self._alert_instructions = alert["instrucoes"]
        self._alert_color = alert["aviso_cor"]
        self._alert_updated = alert["alterado"]
        self._alert_finished = alert["encerrado"]
        self._alert_future = alert["future"]
        self._alert_start_date = datetime.strptime(alert["inicio"], DATE_FORMAT)
        self._alert_end_date = datetime.strptime(alert["fim"], DATE_FORMAT)
        self._alert_sequence = alert["id_sequencia"]
        self._alert_url = f"https://alertas2.inmet.gov.br/{self._alert_id}"

        self._attr_name = f"{self._alert_id} {self._description} {self._alert_severity}"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        return self._alert_id

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend, if any."""
        if self._description and self._description in ICONS:
            return ICONS[self._description]
        return ALERT_ICON

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the device state attributes."""
        return {
            key: value
            for key, value in (
                (ATTR_ALERT_ID, self._alert_id),
                (ATTR_ALERT_DESCRIPTION, self._description),
                (ATTR_ALERT_SEVERITY, self._alert_severity),
                (ATTR_ALERT_SEVERITY_ID, self._alert_severity_id),
                (ATTR_ALERT_RISKS, self._alert_risks),
                (ATTR_ALERT_INSTRUCTIONS, self._alert_instructions),
                (ATTR_ALERT_COLOR, self._alert_color),
                (ATTR_ALERT_UPDATED, self._alert_updated),
                (ATTR_ALERT_FINISHED, self._alert_finished),
                (ATTR_ALERT_FUTURE, self._alert_future),
                (ATTR_ALERT_START_DATE, self._alert_start_date),
                (ATTR_ALERT_END_DATE, self._alert_end_date),
                (ATTR_ALERT_SEQUENCE, self._alert_sequence),
                (ATTR_ALERT_URL, self._alert_url),
            )
            if value or isinstance(value, bool)
        }

    def _haversine(self):
        home_lat = self.hass.config.latitude
        home_lon = self.hass.config.longitude
        alert_lat = self._attr_latitude
        alert_lon = self._attr_longitude

        # Converter graus para radianos
        home_lat, home_lon, alert_lat, alert_lon = map(
            math.radians, [home_lat, home_lon, alert_lat, alert_lon]
        )

        # Diferenças entre os pontos
        dlat = alert_lat - home_lat
        dlon = alert_lon - home_lon

        # Aplicando a fórmula de Haversine
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(home_lat) * math.cos(alert_lat) * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # Raio da Terra em quilômetros
        r = 6371.0

        # Distância em quilômetros
        return r * c

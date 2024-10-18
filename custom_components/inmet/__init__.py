"""The InMet Alerts integration."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CODE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_SCAN_INTERVAL,
    UnitOfLength,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util.unit_conversion import DistanceConverter
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from .const import DOMAIN, FEED, PLATFORMS  # noqa: F401
from .feed_manager import InMetFeedManager
from .status_update import StatusUpdate

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the InMet component as config entry."""
    _LOGGER.debug("Starting InMet alerts (async_setup_entry): %s", DOMAIN)
    hass.data.setdefault(DOMAIN, {})
    feeds = hass.data[DOMAIN].setdefault(FEED, {})

    city_code = config_entry.data[CONF_CODE]
    if hass.config.units is US_CUSTOMARY_SYSTEM:
        city_code = DistanceConverter.convert(
            city_code, UnitOfLength.MILES, UnitOfLength.KILOMETERS
        )
    # Create feed entity manager for all platforms.
    manager = InMetEntityManager(hass, config_entry, city_code)
    feeds[config_entry.entry_id] = manager
    _LOGGER.debug("Feed entity manager added for %s", config_entry.entry_id)
    await manager.async_init()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an InMet component config entry."""
    _LOGGER.debug("Unloading InMet alerts (async_unload_entry): %s", DOMAIN)
    manager: InMetEntityManager = hass.data[DOMAIN][FEED].pop(entry.entry_id)
    await manager.async_stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


class InMetEntityManager:
    """Feed Entity Manager for InMet feed."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, radius_in_km: float
    ) -> None:
        """Initialize the Feed Entity Manager."""
        self._hass = hass
        self._config_entry = config_entry

        city_code = config_entry.data[CONF_CODE]
        websession = aiohttp_client.async_get_clientsession(hass)

        self._feed_manager = InMetFeedManager(
            websession,
            self._generate_entity,
            self._update_entity,
            self._remove_entity,
            city_code,
            status_async_callback=self._status_update,
        )
        self._config_entry_id = config_entry.entry_id
        self._scan_interval = timedelta(seconds=config_entry.data[CONF_SCAN_INTERVAL])
        self._track_time_remove_callback: Callable[[], None] | None = None
        self._status_info: StatusUpdate | None = None
        self.listeners: list[Callable[[], None]] = []

    async def async_init(self) -> None:
        """Schedule initial and regular updates based on configured time interval."""

        await self._hass.config_entries.async_forward_entry_setups(
            self._config_entry, PLATFORMS
        )

        async def update(event_time: datetime) -> None:
            """Update."""
            await self.async_update()

        # Trigger updates at regular intervals.
        self._track_time_remove_callback = async_track_time_interval(
            self._hass, update, self._scan_interval
        )

        _LOGGER.debug("Feed entity manager initialized")

    async def async_update(self) -> None:
        """Refresh data."""
        await self._feed_manager.update()
        _LOGGER.debug("Feed entity manager updated")

    async def async_stop(self) -> None:
        """Stop this feed entity manager from refreshing."""
        for unsub_dispatcher in self.listeners:
            unsub_dispatcher()
        self.listeners = []
        if self._track_time_remove_callback:
            self._track_time_remove_callback()
        _LOGGER.debug("Feed entity manager stopped")

    @callback
    def async_event_new_entity(self) -> str:
        """Return manager specific event to signal new entity."""
        return f"inmet_new_geolocation_{self._config_entry_id}"

    def get_entry(self, alert_id: str) -> str | None:
        """Get feed entry by external id."""
        return self._feed_manager.get(alert_id)

    def status_info(self) -> StatusUpdate | None:
        """Return latest status update info received."""
        return self._status_info

    async def _generate_entity(self, alert_id: str) -> None:
        """Generate new entity."""
        async_dispatcher_send(
            self._hass,
            self.async_event_new_entity(),
            self,
            self._config_entry.unique_id,
            alert_id,
        )

    async def _update_entity(self, alert_id: str) -> None:
        """Update entity."""
        async_dispatcher_send(self._hass, f"inmet_update_{alert_id}")

    async def _remove_entity(self, alert_id: str) -> None:
        """Remove entity."""
        async_dispatcher_send(self._hass, f"inmet_delete_{alert_id}")

    async def _status_update(self, status_info: StatusUpdate) -> None:
        """Propagate status update."""
        _LOGGER.debug("Status update received: %s", status_info)
        self._status_info = status_info
        async_dispatcher_send(self._hass, f"inmet_status_{self._config_entry_id}")

    def latitude(self) -> float | None:
        """Get the latitude."""
        return float(self._config_entry.data[CONF_LATITUDE])

    def longitude(self) -> float | None:
        """Get the longitude."""
        return float(self._config_entry.data[CONF_LONGITUDE])

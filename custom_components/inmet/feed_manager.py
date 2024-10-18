"""Feed Manager for InMet feed."""

from __future__ import annotations

from abc import ABC
from collections.abc import Awaitable, Callable
from datetime import datetime
import logging

import aiohttp
from aiohttp import ClientSession

from .status_update import StatusUpdate

_LOGGER = logging.getLogger(__name__)


class InMetAlert(ABC):
    """InMet Feed class."""

    def __init__(self, alert: dict) -> None:
        """Initialize the alert."""
        self._alert = alert

    def alert_ids(self) -> set | None:
        """Get all alert ids."""
        alerts = self._alert["alerts"]

        return {alert["id"] for alert in alerts}

    def get(self, alert_id: str) -> dict | None:
        """Get a specific alert."""
        return next(
            (alert for alert in self._alert["alerts"] if alert["id"] == alert_id),
            None,
        )


class InMetFeedManager:
    """Feed Manager for InMet feed."""

    def __init__(
        self,
        websession: ClientSession,
        generate_async_callback: Callable[[str], Awaitable[None]],
        update_async_callback: Callable[[str], Awaitable[None]],
        remove_async_callback: Callable[[str], Awaitable[None]],
        city_code: str,
        status_async_callback: Callable[[InMetAlert], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize the InMet Feed Manager."""
        _LOGGER.info("Init InMet FeedManager")
        self._websession = websession
        self._managed_alerts_ids: set = set()
        self._city_code = city_code
        self._last_update: datetime | None = None
        self._alerts: InMetAlert | None = None
        self._generate_async_callback: Callable[[str], Awaitable[None]] = (
            generate_async_callback
        )
        self._update_async_callback: Callable[[str], Awaitable[None]] = (
            update_async_callback
        )
        self._remove_async_callback: Callable[[str], Awaitable[None]] = (
            remove_async_callback
        )
        self._status_async_callback: Callable[[InMetAlert], Awaitable[None]] = (
            status_async_callback
        )

    async def update(self):
        """Update the feed and then update connected entities."""
        _LOGGER.info("Update")

        payload = await self._fetch_data()

        if payload:
            self._alerts = self._filter_payload(payload)
            self._last_update = datetime.now()

            count_created: int = 0
            count_updated: int = 0
            count_removed: int = 0

            alert_ids = self._alerts.alert_ids()

            total = len(alert_ids)

            count_removed = await self._update_feed_remove_entries(alert_ids)
            count_updated = await self._update_feed_update_entries(alert_ids)
            count_created = await self._update_feed_create_entries(alert_ids)

            await self._status_update(
                total, count_created, count_updated, count_removed
            )

    def get(self, alert_id: str) -> dict | None:
        """Get an entry."""
        _LOGGER.info("Getting alert id: %s", alert_id)

        return self._alerts.get(alert_id)

    async def _fetch_data(self) -> dict | None:
        """Fetch city details from external server."""
        url = "https://apiprevmet3.inmet.gov.br/avisos/ativos"
        try:
            async with self._websession.get(url) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to fetch details for city code: %s", self._city_code
                    )
                    return None
                return await response.json()
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching city details: %s", err)
            return None

    def _filter_payload(self, payload: dict) -> InMetAlert:
        """Filter the city_code."""
        response = {}
        response["state"] = 0
        response["alerts"] = []

        today = payload["hoje"]
        city_code: str = str(self._city_code)
        for alert in today:
            geocodes = alert["geocodes"].split(",")

            if city_code in geocodes:
                alert["future"] = False
                response["alerts"].append(alert)

        futuro = payload["futuro"]
        for alert in futuro:
            geocodes = alert["geocodes"].split(",")

            if city_code in geocodes:
                alert["future"] = True
                response["alerts"].append(alert)

        response["state"] = len(response["alerts"])
        return InMetAlert(response)

    async def _update_feed_remove_entries(self, alert_ids: set[str]) -> int:
        """Remove entities after feed update."""
        remove_external_ids: set[str] = self._managed_alerts_ids.difference(alert_ids)
        count_removed = len(remove_external_ids)
        await self._remove_entities(remove_external_ids)
        return count_removed

    async def _update_feed_update_entries(self, alert_ids: set[str]) -> int:
        """Update entities after feed update."""
        update_external_ids: set[str] = self._managed_alerts_ids.intersection(alert_ids)
        count_updated = len(update_external_ids)
        await self._update_entities(update_external_ids)
        return count_updated

    async def _update_feed_create_entries(self, alert_ids: set[str]) -> int:
        """Create entities after feed update."""
        create_external_ids: set[str] = alert_ids.difference(self._managed_alerts_ids)
        count_created = len(create_external_ids)
        await self._generate_new_entities(create_external_ids)
        return count_created

    async def _generate_new_entities(self, alert_ids: set[str]):
        """Generate new entities for events."""
        for alert_id in alert_ids:
            await self._generate_async_callback(alert_id)
            _LOGGER.debug("New entity added %s", alert_id)
            self._managed_alerts_ids.add(alert_id)

    async def _update_entities(self, alert_ids: set[str]):
        """Update entities."""
        for alert_id in alert_ids:
            _LOGGER.debug("Existing entity found %s", alert_id)
            await self._update_async_callback(alert_id)

    async def _remove_entities(self, alert_ids: set[str]):
        """Remove entities."""
        for alert_id in alert_ids:
            _LOGGER.debug("Entity not current anymore %s", alert_id)
            self._managed_alerts_ids.remove(alert_id)
            await self._remove_async_callback(alert_id)

    async def _status_update(
        self, total: int, count_created: int, count_updated: int, count_removed: int
    ):
        """Provide status update."""
        if self._status_async_callback:
            s = StatusUpdate(
                "status",
                None,
                None,
                None,
                total,
                count_created,
                count_removed,
                count_updated,
            )
            await self._status_async_callback(s)

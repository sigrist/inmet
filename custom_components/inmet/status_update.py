"""Status Update."""

from __future__ import annotations

from datetime import datetime


class StatusUpdate:
    """Status Update class."""

    def __init__(
        self,
        status: str,
        last_update: datetime | None,
        last_update_successful: datetime | None,
        last_timestamp: datetime | None,
        total: int,
        created: int,
        updated: int,
        removed: int,
    ) -> None:
        """Initialise this status update."""
        self._status: str = status
        self._last_update: datetime | None = last_update
        self._last_update_successful: datetime | None = last_update_successful
        self._last_timestamp: datetime | None = last_timestamp
        self._total: int = total
        self._created: int = created
        self._updated: int = updated
        self._removed: int = removed

    def __repr__(self):
        """Return string representation of this entry."""
        return f"<{self.__class__.__name__}({self.status}@{self.last_update})>"

    @property
    def status(self) -> str:
        """Return the status."""
        return self._status

    @property
    def last_update(self) -> datetime | None:
        """Return the time when the feed was last updated."""
        return self._last_update

    @property
    def last_update_successful(self) -> datetime | None:
        """Return the time when the feed was last updated successfully."""
        return self._last_update_successful

    @property
    def last_timestamp(self) -> datetime | None:
        """Return the timestamp the latest entry in the feed."""
        return self._last_timestamp

    @property
    def total(self) -> int:
        """Return the total number of managed entries."""
        return self._total

    @property
    def created(self) -> int:
        """Return the number of created entries."""
        return self._created

    @property
    def updated(self) -> int:
        """Return the number of updated entries."""
        return self._updated

    @property
    def removed(self) -> int:
        """Return the number of removed entries."""
        return self._removed

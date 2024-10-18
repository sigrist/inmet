"""Define constants for the InMet integration."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "inmet"

PLATFORMS = [Platform.GEO_LOCATION, Platform.SENSOR]

FEED = "feed"

DEFAULT_ICON = "mdi:check"
ALERT_ICON = "mdi:alert"
DEFAULT_CODE = "3509502"  # Campinas
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)

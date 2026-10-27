"""
Constants for ANWB Charge & Fuel.
"""

DOMAIN = "anwb_charge_and_fuel"

#
# Config Flow
#

CONF_DEVICE_TRACKER = "device_tracker"
CONF_ORS_API_KEY = "ors_api_key"

#
# Entity instellingen
#

CONF_SEARCH_TYPE = "search_type"
CONF_FUEL_TYPE = "fuel_type"
CONF_CHARGER_TYPE = "charger_type"
CONF_LOCATION_SOURCE = "location_source"
CONF_RADIUS = "radius"
CONF_DESTINATION = "destination"

#
# Defaults
#

DEFAULT_RADIUS = 10

DEFAULT_SEARCH_TYPE = "fuel"
DEFAULT_FUEL_TYPE = "euro95"
DEFAULT_CHARGER_TYPE = "all"
DEFAULT_LOCATION_SOURCE = "current_location"

#
# Grenzen
#

MIN_RADIUS = 1
MAX_RADIUS = 100

#
# Select opties
#

SEARCH_TYPES = [
    "fuel",
    "charger",
]

FUEL_TYPES = [
    "euro95",
    "diesel",
    "lpg",
]

CHARGER_TYPES = [
    "all",
    "ac",
    "fast",
    "ultrafast",
]

LOCATION_SOURCES = [
    "current_location",
    "destination",
    "home",
    "work",
]

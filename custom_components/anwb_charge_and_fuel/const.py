"""
Constants for ANWB Charge & Fuel.
"""

DOMAIN = "anwb_charge_and_fuel"

CONF_DEVICE_TRACKER = "device_tracker"
CONF_ORS_API_KEY = "ors_api_key"

DEFAULT_RADIUS = 10

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

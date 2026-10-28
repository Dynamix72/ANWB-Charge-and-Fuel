"""
Constants for ANWB Charge & Fuel.
"""

DOMAIN = "anwb_charge_and_fuel"

#
# Config Flow
#

CONF_DEVICE_TRACKER = "device_tracker"
CONF_ORS_API_KEY = "ors_api_key"
CONF_DATA_MODE = "data_mode"

#
# Defaults
#

DEFAULT_RADIUS = 10
DEFAULT_DATA_MODE = "both"

DEFAULT_FUEL_TYPE = "euro95"
DEFAULT_CHARGER_TYPE = "all"

#
# Grenzen
#

MIN_RADIUS = 1
MAX_RADIUS = 100

#
# Data mode
#

DATA_MODES = [
    "charge",
    "fuel",
    "both",
]

#
# Select opties
#

FUEL_TYPES = [
    "euro95",
    "diesel",
    "superplus",
    "lpg",
]

CHARGER_TYPES = [
    "all",
    "ac",
    "fast",
    "ultrafast",
]



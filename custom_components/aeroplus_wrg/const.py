DOMAIN = "aeroplus_wrg"
PLATFORMS = ["switch", "sensor", "select", "number"]

DEFAULT_PORT = 443
DEFAULT_USE_SSL = True
WS_PATH = "/WebSocket"

DATA_CLIENT = "client"
DATA_COORDINATOR = "coordinator"
DATA_SPEED_MEMORY = "speed_memory"

UPDATE_INTERVAL_SECONDS = 10
HEARTBEAT_SECONDS = 10

# Keys as reported by getDeviceState()/getDeviceParams()/getDevice(), flattened
# with dot-separated paths (see device.flatten). Different firmware/device
# variants have been observed to report these under slightly different keys,
# so each sensor checks a list of candidates in order.
KEY_DEVICE_ACTIVE = "deviceactive"
KEYS_TEMPERATURE_INDOOR = ["airbase.temperature.indoor", "temperature.indoor"]
KEYS_TEMPERATURE_OUTDOOR = ["airbase.temperature.outdoor", "temperature.outdoor"]
KEYS_HUMIDITY_INDOOR = ["airbase.humidity.indoor", "humidity.indoor"]
KEYS_HUMIDITY_OUTDOOR = ["airbase.humidity.outdoor", "humidity.outdoor"]
KEYS_CO2 = ["airquality.co2content", "co2_value"]

# Confirmed against a live device's getDeviceParams response (2026-09-23):
# fanmode/fanpower/automode/automode_maxairflow are all top-level
# getDeviceParams fields (unlike deviceactive, they are read/written flat, no
# "devicestate" nesting). automode is a genuinely separate boolean field -
# fanmode never actually takes an "AUTO" value on this hardware (that was a
# wrong assumption from the ioBroker.siegenia reference project, which caused
# a "Siegenia error: incorrect_format" when written).
KEY_FAN_MODE = "fanmode"
KEY_FAN_POWER = "fanpower"
KEY_AUTOMODE = "automode"
KEY_AUTOMODE_MAX_AIRFLOW = "automode_maxairflow"

FAN_MODE_LABELS = {
    "IN": "Zuluft",
    "OUT": "Abluft",
    "IN_OUT": "Zu-/Abluft",
    "IN_OUT_WRG": "Zu-/Abluft mit Wärmerückgewinnung",
}

DOMAIN = "aeroplus_wrg"
PLATFORMS = ["switch", "sensor", "select", "number"]

DEFAULT_PORT = 443
DEFAULT_USE_SSL = True
WS_PATH = "/WebSocket"

DATA_CLIENT = "client"
DATA_COORDINATOR = "coordinator"

UPDATE_INTERVAL_SECONDS = 10
HEARTBEAT_SECONDS = 10

# Keys as reported by getDeviceState()/getDeviceParams()/getDevice(), flattened
# with dot-separated paths (see device.flatten). Different firmware/device
# variants have been observed to report these under slightly different keys,
# so each sensor checks a list of candidates in order.
KEY_DEVICE_ACTIVE = "deviceactive"
KEYS_TEMPERATURE_INDOOR = ["airbase.temperature.indoor", "temperature.indoor"]
KEYS_TEMPERATURE_OUTDOOR = ["airbase.temperature.outdoor", "temperature.outdoor"]
KEYS_CO2 = ["airquality.co2content", "co2_value"]

# Confirmed against Apollon77/ioBroker.siegenia's protocol map for device type
# 14 (AEROPLUS): fanmode/fanpower/automode_maxairflow are top-level
# getDeviceParams fields (unlike deviceactive, they are read/written flat, no
# "devicestate" nesting).
KEY_FAN_MODE = "fanmode"
KEY_FAN_POWER = "fanpower"
KEY_AUTOMODE_MAX_AIRFLOW = "automode_maxairflow"

# fanmode is transmitted as one of these strings; AUTO is a value of fanmode,
# not a separate on/off flag.
FAN_MODE_AUTO = "AUTO"
FAN_MODE_LABELS = {
    "IN": "Zuluft",
    "OUT": "Abluft",
    "IN_OUT": "Zu-/Abluft",
    "IN_OUT_WRG": "Zu-/Abluft mit Wärmerückgewinnung",
    "AUTO": "Automatik",
}
DEFAULT_MANUAL_FAN_MODE = "IN_OUT_WRG"

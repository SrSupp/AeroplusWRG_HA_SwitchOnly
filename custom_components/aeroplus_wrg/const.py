DOMAIN = "aeroplus_wrg"
PLATFORMS = ["switch", "sensor"]

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
KEYS_TEMPERATURE_INDOOR = ["temperature.indoor", "airbase.temperature.indoor"]
KEYS_TEMPERATURE_OUTDOOR = ["temperature.outdoor", "airbase.temperature.outdoor"]
KEYS_CO2 = ["airquality.co2content", "co2_value"]

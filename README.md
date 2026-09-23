# Aeroplus WRG for Home Assistant

> **Disclaimer:** This entire integration — code, comments, and this README —
> was written by [Claude](https://claude.com/claude-code) (Anthropic's AI
> coding assistant), based on the repository owner's instructions and tested
> against their own hardware over the course of an interactive session. It is
> provided **as-is, with absolutely no warranty of any kind**. The author
> makes no guarantee that it works correctly, safely, or at all on your
> setup. Review the code yourself before relying on it, especially since it
> controls physical ventilation hardware in a home. Use entirely at your own
> risk.

Home Assistant integration for Siegenia Aeroplus WRG smart ventilation
modules. Based on
[rikbootsman/home-assistant-siegenia-Aeroplus-WRG](https://github.com/rikbootsman/home-assistant-siegenia-Aeroplus-WRG)
(incl. the on/off fix from [PR #5](https://github.com/rikbootsman/home-assistant-siegenia-Aeroplus-WRG/pull/5)),
with field names verified against a real Aeroplus WRG device (not just
documentation or reference projects).

**Entities:**
- `switch` **Power** – turns the device on/off (`devicestate.deviceactive`)
- `switch` **Automatikmodus** (auto mode) – turns automatic operation on/off
  (`automode`, a field of its own, independent of the ventilation mode)
- `select` **Lüftungsmodus** (ventilation mode) – supply air / exhaust air /
  supply+exhaust / supply+exhaust with heat recovery (`fanmode`)
- `number` **Lüftungsgeschwindigkeit** (fan speed) – target fan level in %;
  controls `fanpower` while auto mode is off, and `automode_maxairflow` (auto
  mode's upper limit) while auto mode is on — one control instead of two.
  The last value set is remembered per mode and re-applied automatically
  whenever the auto mode switch is toggled, persisted via Home Assistant's
  storage helper (`.storage/`), so it survives restarts
- `sensor` **Feedback Lüftergeschwindigkeit** (fan speed feedback) – actual
  running fan level in % (`fanpower`, read-only, 0% while off)
- `sensor` indoor/outdoor **temperature**, indoor/outdoor **humidity**,
  **CO2** (CO2 becomes `unavailable` while off, since it's no longer being
  measured then)

Entity and friendly names are in German by design, matching how the
integration author and the physical devices are set up. Timers, lighting,
sash/window control and similar features of other Siegenia device types are
not included: they don't apply to the Aeroplus WRG, or are meant to stay
controlled via the Siegenia app on purpose.

## Why a custom on/off command is needed

The device reports its on/off state via `getDeviceState` as a flat
`deviceactive` field. `setDeviceParams` expects that value nested under
`devicestate` when writing it, though:

```json
{"command": "setDeviceParams", "params": {"devicestate": {"deviceactive": true}}}
```

Sending `deviceactive` (or `power`/`on`/`enabled`) flat is accepted by the
device but doesn't actually change its state. That's the key fix from the
original project's PR #5, implemented here directly in
[`api.py`](custom_components/aeroplus_wrg/api.py).

## Installation

### Via HACS (recommended)
1. Open HACS → Integrations → menu (⋮) → "Custom repositories"
2. Add this repository (type: Integration)
3. Install "Aeroplus WRG"
4. Restart Home Assistant

### Manual
1. Copy the `custom_components/aeroplus_wrg` folder into your Home
   Assistant's `custom_components` directory
2. Restart Home Assistant

## Setup

1. Settings → Devices & Services → Add Integration
2. Search for "Aeroplus WRG"
3. Enter credentials (the same ones used in the Siegenia app):
   - Host / IP address
   - Username
   - Password
   - Port (default: 443)
   - SSL (default: on)

Each configured device creates:
- `switch.<name>_power`
- `switch.<name>_automatikmodus`
- `select.<name>_luftungsmodus`
- `number.<name>_luftungsgeschwindigkeit`
- `sensor.<name>_feedback_luftergeschwindigkeit`
- `sensor.<name>_indoor_temperature`
- `sensor.<name>_outdoor_temperature`
- `sensor.<name>_indoor_humidity`
- `sensor.<name>_outdoor_humidity`
- `sensor.<name>_co2`

> If a separate `number.<name>_automatikgeschwindigkeit` existed before: it
> disappears with this update (folded into
> `number.<name>_luftungsgeschwindigkeit`, see above) and can be removed
> manually under Settings → Devices & Services → Entities if it shows up as
> "no longer provided".

## Technical details

- Local WebSocket connection (`wss://<host>:<port>/WebSocket`), no cloud
  required
- Updates every 10 seconds via polling, plus an immediate refresh on
  unsolicited push messages from the device
- Tested with Aeroplus WRG modules; other Siegenia devices using the same
  WebSocket protocol should also work for on/off + sensors

### Troubleshooting

Enable debug logging:

```yaml
logger:
  default: info
  logs:
    custom_components.aeroplus_wrg: debug
```

## License

MIT License, see [LICENSE](LICENSE). Based on the MIT-licensed
[home-assistant-siegenia-Aeroplus-WRG](https://github.com/rikbootsman/home-assistant-siegenia-Aeroplus-WRG)
by rikbootsman.

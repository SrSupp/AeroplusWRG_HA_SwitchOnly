# Aeroplus WRG for Home Assistant

Home Assistant Integration für die Siegenia Aeroplus WRG Smart Module.
Basiert auf [rikbootsman/home-assistant-siegenia-Aeroplus-WRG](https://github.com/rikbootsman/home-assistant-siegenia-Aeroplus-WRG)
(inkl. des Ein/Aus-Fixes aus [PR #5](https://github.com/rikbootsman/home-assistant-siegenia-Aeroplus-WRG/pull/5)),
mit Feldnamen, die gegen ein echtes Aeroplus-WRG-Gerät verifiziert wurden
(nicht nur gegen Dokumentation/Referenzprojekte).

**Entities:**
- `switch` **Power** – Gerät ein-/ausschalten (`devicestate.deviceactive`)
- `switch` **Automatikmodus** – Automatikbetrieb ein-/ausschalten (`automode`,
  ein eigenständiges Feld, unabhängig vom Lüftungsmodus)
- `select` **Lüftungsmodus** – Zuluft / Abluft / Zu-/Abluft / Zu-/Abluft mit
  Wärmerückgewinnung (`fanmode`)
- `number` **Lüftungsgeschwindigkeit** – Ziel-Lüfterstufe in %; steuert bei
  ausgeschaltetem Automatikmodus `fanpower`, bei eingeschaltetem Automatikmodus
  `automode_maxairflow` (die Obergrenze der Automatik) – ein Regler statt zwei.
  Der zuletzt gesetzte Wert wird pro Modus gemerkt und beim Umschalten des
  Automatikmodus-Schalters automatisch wieder angewendet (nur im
  Integrations-Speicher, geht bei einem HA-Neustart verloren)
- `sensor` **Feedback Lüftergeschwindigkeit** – tatsächlich laufende Lüfterstufe
  in % (`fanpower`, read-only, 0 % wenn ausgeschaltet)
- `sensor` **Innen-/Außentemperatur**, **Innen-/Außenfeuchtigkeit**, **CO₂**
  (CO₂ wird `unavailable` wenn ausgeschaltet, da dann nicht mehr gemessen wird)

Timer, Beleuchtung, Sash-/Fenstersteuerung und ähnliche Funktionen anderer
Siegenia-Gerätetypen sind nicht enthalten, da sie für Aeroplus WRG nicht
zutreffen bzw. bewusst weiterhin über die Siegenia-App laufen sollen.

## Warum ein eigener On/Off-Befehl nötig ist

Das Gerät meldet den Ein/Aus-Zustand über `getDeviceState` flach als
`deviceactive`. `setDeviceParams` erwartet den Wert beim Schreiben aber
verschachtelt unter `devicestate`:

```json
{"command": "setDeviceParams", "params": {"devicestate": {"deviceactive": true}}}
```

Schickt man `deviceactive` (oder `power`/`on`/`enabled`) flach, akzeptiert das
Gerät den Aufruf zwar, ändert den Zustand aber nicht. Das ist der zentrale Fix
aus PR #5 des Originalprojekts und wird hier direkt in [`api.py`](custom_components/aeroplus_wrg/api.py)
umgesetzt.

## Installation

### Über HACS (empfohlen)
1. HACS öffnen → Integrationen → Menü (⋮) → "Benutzerdefinierte Repositories"
2. Dieses Repository hinzufügen (Typ: Integration)
3. "Aeroplus WRG" installieren
4. Home Assistant neu starten

### Manuell
1. Ordner `custom_components/aeroplus_wrg` in das `custom_components`-Verzeichnis
   der Home-Assistant-Installation kopieren
2. Home Assistant neu starten

## Einrichtung

1. Einstellungen → Geräte & Dienste → Integration hinzufügen
2. "Aeroplus WRG" suchen
3. Zugangsdaten eingeben (dieselben wie in der Siegenia-App):
   - Host / IP-Adresse
   - Benutzername
   - Passwort
   - Port (Standard: 443)
   - SSL (Standard: an)

Für jedes eingerichtete Gerät entstehen:
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

> Falls vorher schon eine separate `number.<name>_automatikgeschwindigkeit`
> vorhanden war: die verschwindet mit diesem Update (aufgegangen in
> `number.<name>_luftungsgeschwindigkeit`, siehe oben) und kann in
> Einstellungen → Geräte & Dienste → Entitäten manuell gelöscht werden, falls
> sie als "nicht mehr bereitgestellt" auftaucht.

## Technische Details

- Lokale WebSocket-Verbindung (`wss://<host>:<port>/WebSocket`), keine Cloud nötig
- Aktualisierung alle 10 Sekunden per Polling, zusätzlich sofortiges Update bei
  unaufgeforderten Push-Nachrichten des Geräts
- Getestet mit Aeroplus-WRG-Modulen; andere Siegenia-Geräte mit demselben
  WebSocket-Protokoll sollten für Ein/Aus + Sensoren ebenfalls funktionieren

### Fehlersuche

Debug-Logging aktivieren:

```yaml
logger:
  default: info
  logs:
    custom_components.aeroplus_wrg: debug
```

## Lizenz

MIT License, siehe [LICENSE](LICENSE). Basierend auf dem MIT-lizenzierten
[home-assistant-siegenia-Aeroplus-WRG](https://github.com/rikbootsman/home-assistant-siegenia-Aeroplus-WRG)
von rikbootsman.

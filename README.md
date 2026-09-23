# Aeroplus WRG for Home Assistant (Switch Only)

Schlanke Home Assistant Integration für die Siegenia Aeroplus WRG Smart Module.
Basiert auf [rikbootsman/home-assistant-siegenia-Aeroplus-WRG](https://github.com/rikbootsman/home-assistant-siegenia-Aeroplus-WRG)
(inkl. des Ein/Aus-Fixes aus [PR #5](https://github.com/rikbootsman/home-assistant-siegenia-Aeroplus-WRG/pull/5)),
aber bewusst auf das Nötigste reduziert:

- **Nur Ein/Aus** – ein einzelner Schalter (`switch`) zum Ein-/Ausschalten des Geräts.
  Alle anderen Modi (Automatik, Lüfterstufe, Timer, …) werden weiterhin über die
  Siegenia-App gesteuert und von dieser Integration nicht angefasst.
- **Sensoren**: Innentemperatur, Außentemperatur und CO₂-Gehalt werden nach
  Home Assistant übertragen.

Alle anderen Entitäten (Lüfter-Prozentsteuerung, Automatik-Schalter, Leistungs-Zahl,
Rohzustand, Verbindungsstatus) aus dem Originalprojekt sind absichtlich **nicht**
enthalten.

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
3. "Aeroplus WRG (Switch Only)" installieren
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
- `switch.<name>_power` – Ein/Aus
- `sensor.<name>_indoor_temperature`
- `sensor.<name>_outdoor_temperature`
- `sensor.<name>_co2`

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

## Icon in der Home-Assistant-Oberfläche

Home Assistant und HACS holen Integrations-Icons zentral aus dem öffentlichen
[home-assistant/brands](https://github.com/home-assistant/brands)-Repository
(anhand der Domain `aeroplus_wrg`) – es reicht nicht, ein Icon einfach in
`custom_components/aeroplus_wrg` abzulegen.

Unter [`brand_assets/custom_integrations/aeroplus_wrg`](brand_assets/custom_integrations/aeroplus_wrg)
liegt ein fertiges, generisches Lüfter-Icon (`icon.png` 256×256, `icon@2x.png`
512×512) im von `home-assistant/brands` geforderten Format. Um es sichtbar zu
machen:

1. [home-assistant/brands](https://github.com/home-assistant/brands) forken
2. Den Ordner `brand_assets/custom_integrations/aeroplus_wrg` aus diesem
   Repository 1:1 nach `custom_integrations/aeroplus_wrg` im Fork kopieren
3. Pull Request gegen `home-assistant/brands` öffnen
4. Nach Merge (kann etwas dauern, liegt bei den dortigen Maintainern) taucht
   das Icon automatisch in Home Assistant und HACS auf – ein Neustart oder
   Cache-Leeren im Frontend reicht danach

## Lizenz

MIT License, siehe [LICENSE](LICENSE). Basierend auf dem MIT-lizenzierten
[home-assistant-siegenia-Aeroplus-WRG](https://github.com/rikbootsman/home-assistant-siegenia-Aeroplus-WRG)
von rikbootsman.

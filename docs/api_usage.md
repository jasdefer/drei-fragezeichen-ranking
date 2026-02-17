# Dreimetadaten API – Nutzung im Projekt

Dieses Dokument beschreibt die Rolle der Dreimetadaten API in diesem Repository und den aktuellen Implementierungsstand des Wrappers in `bot/dreimetadaten_api.py`.

## Warum ein API-Wrapper?

Das Projekt trennt bewusst **Stammdaten** (extern) von **Projektzustand** (lokale TSV-Dateien):

- Episoden-Stammdaten kommen aus der Dreimetadaten API
- Poll- und Ratingdaten liegen versioniert im Repository
- Auswertungslogik bleibt reproduzierbar und unabhängig von einer eigenen Datenbank

Der Wrapper kapselt diese Zugriffsschicht und sorgt für einheitliches Fehlerhandling und Logging.

## API-Zugriffspunkt

Genutzter Zugriffspunkt der Dreimetadaten API:

- `https://api.dreimetadaten.de/db.json`

## Aktuell umgesetzte Funktionen

Das Modul stellt drei zentrale Funktionen bereit:

1. `run_query(query, timeout=30, max_retries=3)`
   - generischer SQL-basierter Zugriff
   - liefert API-Ergebnisse als Liste von Dictionaries

2. `fetch_all_episodes()`
   - lädt die vollständige Episodenliste als Nummern
   - Rückgabe pro Eintrag: `nummer`

3. `fetch_episode_metadata(nummer)`
   - lädt Metadaten für eine konkrete Folge
   - Rückgabe: `nummer`, `titel`, `beschreibung`, `urlCoverApple`
   - Rückgabe `None`, wenn keine Episode gefunden wurde

## Fehlerbehandlung und Robustheit

Der Wrapper ist auf robuste Nutzung in Automationskontexten ausgelegt:

- einheitliche Exception-Hierarchie (`APIError`, `APITimeoutError`, `APIResponseError`)
- Retry-Logik mit exponentiellem Backoff bei temporären Fehlern
- strukturierte Log-Ausgaben für erfolgreiche Aufrufe und Fehlerfälle

Damit bleibt der Aufrufer-Code schlank, weil Netzwerk- und Antwortfehler an einer Stelle zentral behandelt werden.

## Abgrenzung zu lokalen Daten

Nicht Teil des API-Wrappers sind:

- Persistenz von Poll- oder Ratingdaten
- Modellberechnung (Bradley-Terry)
- Ablauf-Orchestrierung (z. B. Posting, Zeitplanung, Veröffentlichung)

Diese Verantwortung liegt in anderen Modulen und in den geplanten Automationsschritten.

## Hinweise zum Betrieb

- API-Tests (`tests/test_dreimetadaten_api.py`) benötigen Internetzugriff
- externe Daten können sich im Zeitverlauf ändern
- konkrete Titel-Assertions können dadurch langfristig driftanfällig sein

## Weiterführende Links

- API-Dokumentation: https://api.dreimetadaten.de/
- Dreimetadaten-Projekt: https://dreimetadaten.de/

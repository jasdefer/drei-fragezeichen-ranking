# Dreimetadaten API Usage

Dieses Dokument beschreibt die Nutzung der Dreimetadaten API und des API-Wrappers in diesem Projekt.

## API-Endpoint

Die Dreimetadaten API stellt eine SQL-basierte Schnittstelle zur Verfügung:

```
https://api.dreimetadaten.de/db.json
```

## Grundlegende Verwendung

### Generic Query-Wrapper

Die Funktion `run_query()` bietet einen generischen Zugriff auf die API. Sie akzeptiert einen SQL-Query-String sowie optionale Parameter für Timeout (Standard: 30 Sekunden) und max_retries (Standard: 3).

### Parameter

- **`query`** (str, erforderlich): SQL-Query-String
- **`timeout`** (int, optional): Request-Timeout in Sekunden (Standard: 30)
- **`max_retries`** (int, optional): Maximale Anzahl von Wiederholungsversuchen bei Fehlern (Standard: 3)

### Rückgabewert

Die Funktion gibt die API-Antwort als Python-Datenstruktur zurück:
- Bei erfolgreichen Queries: Liste von Dictionaries (durch `_shape=array` Parameter)
- Bei Fehlern: wirft entsprechende Exceptions (`APIError`, `APITimeoutError`, `APIResponseError`)

## Helper-Funktionen

Das Modul stellt spezialisierte Helper-Funktionen für häufige Anwendungsfälle bereit:

### Alle Episodennummern laden

```python
from bot.dreimetadaten_api import fetch_all_episodes

episodes = fetch_all_episodes()
# Gibt Liste aller Episoden-Nummern zurück, sortiert nach Folgennummer
```

**Rückgabewert**: Liste von Dictionaries mit Feld:
**Rückgabewert**: Liste von Dictionaries mit Feld:
- `nummer` (int): Folgennummer

**Hinweis**: Diese Funktion lädt nur die Episodennummern. Für vollständige Metadaten einer Episode verwende `fetch_episode_metadata(nummer)`.

### Metadaten einer spezifischen Episode laden

**Verwendung**: `fetch_episode_metadata(nummer)` lädt Metadaten für eine spezifische Episode.

**Parameter**:
- `nummer` (int): Folgennummer der gewünschten Episode

**Rückgabewert**: 
- Dictionary mit Episode-Metadaten:
  - `nummer` (int): Folgennummer
  - `titel` (str): Titel der Folge
  - `beschreibung` (str): Beschreibung der Folge
  - `urlCoverApple` (str): URL zum Cover-Bild
- `None` falls Episode nicht gefunden
FROM serie s
JOIN hörspiel h ON h.hörspielID = s.hörspielID
WHERE s.nummer = {nummer}
```

## Datenbankschema

Die Dreimetadaten API basiert auf folgenden Haupttabellen:

### `serie` Tabelle
- `nummer`: Folgennummer
- `hörspielID`: Fremdschlüssel zur `hörspiel` Tabelle

## Datenbankschema

Die Dreimetadaten API basiert auf folgenden Haupttabellen:

### `serie` Tabelle
- `nummer`: Folgennummer
- `hörspielID`: Fremdschlüssel zur `hörspiel` Tabelle

### `hörspiel` Tabelle
- `hörspielID`: Primärschlüssel
- `titel`: Titel der Folge
- `beschreibung`: Beschreibung der Handlung
- `urlCoverApple`: URL zum Cover-Bild

## Fehlerhandling

Das API-Modul implementiert robustes Fehlerhandling:

### Exception-Typen

- **`APIError`**: Basisklasse für alle API-bezogenen Fehler
- **`APITimeoutError`**: Speziell für Timeout-Fehler
- **`APIResponseError`**: Für fehlerhafte API-Antworten (z.B. ungültiges JSON, HTTP-Fehler)

### Retry-Mechanismus

Bei vorübergehenden Fehlern (Timeouts, Netzwerkfehler) wird automatisch wiederholt:
- Exponentielles Backoff: Wartezeiten von 1s, 2s, 4s, etc.
- Standardmäßig maximal 3 Versuche (konfigurierbar via `max_retries`)

### Logging

Alle API-Operationen werden geloggt:
- **DEBUG**: Detaillierte Query-Informationen und Ergebnisse
- **INFO**: Erfolgreiche Operationen und Zusammenfassungen
- **WARNING**: Nicht-kritische Fehler und Retry-Versuche
- **ERROR**: Kritische Fehler, die zum Abbruch führen

## Best Practices

1. **Timeout-Werte anpassen**: Bei langsamen Verbindungen oder großen Queries den `timeout`-Parameter erhöhen

2. **Retry-Verhalten konfigurieren**: Bei kritischen Operationen `max_retries` erhöhen

3. **Exceptions behandeln**: Immer try-except verwenden, um API-Fehler abzufangen

4. **Logging nutzen**: Logger-Ausgaben beachten für Debugging und Monitoring

5. **Caching erwägen**: Bei häufigen Abfragen gleicher Daten sollte ein Caching-Layer in Betracht gezogen werden

## Verwendungshinweise

Die API bietet drei Hauptfunktionen:

1. **`fetch_all_episodes()`**: Lädt alle Episodennummern
2. **`fetch_episode_metadata(nummer)`**: Lädt Metadaten für eine spezifische Episode
3. **`run_query(query)`**: Führt Custom SQL-Queries aus

Fehlerbehandlung erfolgt über Exception-Typen: `APIError` (Basis), `APITimeoutError`, `APIResponseError`.

## Migration von TSV zu API

Der API-Wrapper ersetzt die bisherige TSV-basierte Episode-Datenhaltung.

### Datenstruktur-Mapping

**fetch_all_episodes()** gibt zurück:
- `nummer` (int): Folgennummer

**fetch_episode_metadata(nummer)** gibt zurück:
- `nummer` (int): Folgennummer
- `titel` (str): Titel der Folge
- `beschreibung` (str): Beschreibung
- `urlCoverApple` (str): Cover-URL

| TSV-Feld | API-Feld | Verfügbar über | Anmerkung |
|----------|----------|----------------|-----------|
| `episode_id` | `nummer` | Beide Funktionen | Folgennummer (int) |
| `title` | `titel` | `fetch_episode_metadata()` | Titel der Folge |
| `description` | `beschreibung` | `fetch_episode_metadata()` | Beschreibung |
| `year` | - | - | Nicht in API enthalten |
| `type` | - | - | Nicht in API enthalten |
| - | `urlCoverApple` | `fetch_episode_metadata()` | Neu: Cover-URL |

**Hinweis**: `fetch_all_episodes()` lädt bewusst nur die Episodennummern für bessere Performance. Vollständige Metadaten können gezielt per `fetch_episode_metadata()` abgerufen werden.

## Weiterführende Ressourcen

- API-Dokumentation: https://api.dreimetadaten.de/
- Projekt-Repository: https://github.com/jasdefer/drei-fragezeichen-ranking
- Dreimetadaten-Projekt: https://dreimetadaten.de/

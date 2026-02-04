# Dreimetadaten API Usage

Dieses Dokument beschreibt die Nutzung der Dreimetadaten API und des API-Wrappers in diesem Projekt.

## API-Endpoint

Die Dreimetadaten API stellt eine SQL-basierte Schnittstelle zur Verfügung:

```
https://api.dreimetadaten.de/db.json
```

## Grundlegende Verwendung

### Generic Query-Wrapper

Die Funktion `run_query()` bietet einen generischen Zugriff auf die API:

```python
from bot.dreimetadaten_api import run_query

# Einfacher SQL-Query
query = "SELECT * FROM serie LIMIT 10"
result = run_query(query)

# Mit optionalen Parametern
result = run_query(
    query,
    timeout=60,        # Timeout in Sekunden
    max_retries=5      # Maximale Wiederholungsversuche
)
```

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

### Alle Episoden laden

```python
from bot.dreimetadaten_api import fetch_all_episodes

episodes = fetch_all_episodes()
# Gibt Liste aller Episoden zurück, sortiert nach Folgennummer
```

**Rückgabewert**: Liste von Dictionaries mit Feldern:
- `nummer` (int): Folgennummer
- `titel` (str): Titel der Folge
- `beschreibung` (str): Beschreibung der Folge
- `urlCoverApple` (str): URL zum Cover-Bild

**Verwendeter Query**:
```sql
SELECT 
    s.nummer,
    h.titel,
    h.beschreibung,
    h.urlCoverApple
FROM serie s
JOIN hörspiel h ON h.hörspielID = s.hörspielID
ORDER BY s.nummer
```

### Metadaten einer spezifischen Episode laden

```python
from bot.dreimetadaten_api import fetch_episode_metadata

episode = fetch_episode_metadata(149)
if episode:
    print(f"Titel: {episode['titel']}")
    print(f"Beschreibung: {episode['beschreibung']}")
```

**Parameter**:
- `nummer` (int): Folgennummer der gewünschten Episode

**Rückgabewert**: 
- Dictionary mit Episode-Metadaten (gleiche Struktur wie `fetch_all_episodes()`)
- `None` falls Episode nicht gefunden

**Verwendeter Query**:
```sql
SELECT 
    s.nummer,
    h.titel,
    h.beschreibung,
    h.urlCoverApple
FROM serie s
JOIN hörspiel h ON h.hörspielID = s.hörspielID
WHERE s.nummer = {nummer}
```

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

## Query-Beispiele

### Beispiel 1: Alle Episoden mit Metadaten

```sql
SELECT 
    s.nummer,
    h.titel,
    h.beschreibung,
    h.urlCoverApple
FROM serie s
JOIN hörspiel h ON h.hörspielID = s.hörspielID
ORDER BY s.nummer
```

API-Aufruf:
```
https://api.dreimetadaten.de/db.json?sql=SELECT%20s.nummer,%20h.titel,%20h.beschreibung,%20h.urlCoverApple%20FROM%20serie%20s%20JOIN%20hörspiel%20h%20ON%20h.hörspielID%20=%20s.hörspielID%20ORDER%20BY%20s.nummer&_shape=array
```

### Beispiel 2: Spezifische Episode (z.B. Folge 149)

```sql
SELECT 
    s.nummer,
    h.titel,
    h.beschreibung,
    h.urlCoverApple
FROM serie s
JOIN hörspiel h ON h.hörspielID = s.hörspielID
WHERE s.nummer = 149
```

API-Aufruf:
```
https://api.dreimetadaten.de/db.json?sql=SELECT%20s.nummer,%20h.titel,%20h.beschreibung,%20h.urlCoverApple%20FROM%20serie%20s%20JOIN%20hörspiel%20h%20ON%20h.hörspielID%20=%20s.hörspielID%20WHERE%20s.nummer%20=%20149&_shape=array
```

### Beispiel 3: Nur Titel und Nummern

```sql
SELECT s.nummer, h.titel
FROM serie s
JOIN hörspiel h ON h.hörspielID = s.hörspielID
ORDER BY s.nummer
```

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

## Beispiel-Code

```python
from bot.dreimetadaten_api import (
    run_query, 
    fetch_all_episodes, 
    fetch_episode_metadata,
    APIError
)
from bot.logger import get_logger

logger = get_logger(__name__)

# Alle Episoden laden mit Fehlerbehandlung
try:
    episodes = fetch_all_episodes()
    logger.info(f"Erfolgreich {len(episodes)} Episoden geladen")
    
    for episode in episodes[:5]:  # Erste 5 Episoden
        print(f"{episode['nummer']}: {episode['titel']}")
        
except APIError as e:
    logger.error(f"Fehler beim Laden der Episoden: {e}")

# Spezifische Episode laden
try:
    episode = fetch_episode_metadata(149)
    if episode:
        print(f"Folge 149: {episode['titel']}")
        print(f"Beschreibung: {episode['beschreibung']}")
    else:
        print("Episode 149 nicht gefunden")
        
except APIError as e:
    logger.error(f"API-Fehler: {e}")

# Custom Query mit erweiterten Optionen
try:
    query = """
    SELECT s.nummer, h.titel 
    FROM serie s 
    JOIN hörspiel h ON h.hörspielID = s.hörspielID 
    WHERE s.nummer > 200
    ORDER BY s.nummer
    LIMIT 10
    """
    
    result = run_query(query, timeout=60, max_retries=5)
    print(f"Gefunden: {len(result)} Episoden über Nummer 200")
    
except APIError as e:
    logger.error(f"Query fehlgeschlagen: {e}")
```

## Migration von TSV zu API

Dieser API-Wrapper ersetzt die bisherige TSV-basierte Episode-Datenhaltung. Die Hauptunterschiede:

### Vorher (TSV):
```python
from bot.tsv_loader import load_episodes

episodes = load_episodes(Path("data/episodes.tsv"))
```

### Nachher (API):
```python
from bot.dreimetadaten_api import fetch_all_episodes

episodes = fetch_all_episodes()
```

### Datenstruktur-Mapping

| TSV-Feld | API-Feld | Anmerkung |
|----------|----------|-----------|
| `episode_id` | `nummer` | Folgennummer (int) |
| `title` | `titel` | Titel der Folge |
| `description` | `beschreibung` | Beschreibung |
| `year` | - | Nicht in API enthalten |
| `type` | - | Nicht in API enthalten |
| - | `urlCoverApple` | Neu: Cover-URL |

**Hinweis**: Felder wie `year` und `type`, die in der TSV-Struktur vorhanden waren, aber nicht von der API bereitgestellt werden, müssen ggf. anderweitig ermittelt oder entfernt werden.

## Weiterführende Ressourcen

- API-Dokumentation: https://api.dreimetadaten.de/
- Projekt-Repository: https://github.com/jasdefer/drei-fragezeichen-ranking
- Dreimetadaten-Projekt: https://dreimetadaten.de/

# Tests

Dieser Ordner enthält automatisierte Tests für das Drei ??? Community Ranking Projekt.

## Struktur

Die Tests sind nach Modulen organisiert:
- `test_bradley_terry.py` - Unit-Tests für die Modelllogik (offline-fähig)
- `test_matchmaking.py` - Unit-Tests für Seed-/Frontier-Logik im Matchmaking
- `test_dreimetadaten_api.py` - Integrationstests für das API-Wrapper-Modul (Netzwerk erforderlich)

## Tests ausführen

```bash
# Alle Tests ausführen
python -m pytest tests/

# Einzelne Test-Datei ausführen
python -m pytest tests/test_dreimetadaten_api.py

# Mit verbose Output
python -m pytest -v tests/

# Spezifischen Test ausführen
python -m pytest tests/test_dreimetadaten_api.py::test_fetch_all_episodes
```

## Test-Kategorien

### API-Tests (`test_dreimetadaten_api.py`)

Diese Tests validieren die Funktionalität des Dreimetadaten API-Wrappers:

- **Datenintegrität**: Prüft, ob die API die erwartete Anzahl und Struktur von Episoden zurückgibt
- **Metadaten-Vollständigkeit**: Validiert, dass alle erforderlichen Metadaten-Felder vorhanden und nicht leer sind
- **Spezifische Episoden**: Testet bekannte Episoden auf korrekte Daten (z.B. Episode 149: "Der namenlose Gegner")

**Hinweis**: Diese Tests führen echte API-Aufrufe gegen die Dreimetadaten API durch und benötigen daher eine Internetverbindung.

### Bradley-Terry-Tests (`test_bradley_terry.py`)

Diese Tests prüfen die Kernlogik der Auswertung ohne Dateisystem- oder Netzwerkzugriffe:

- Konnektivitätsregeln (inkl. Episode-1-Komponente)
- Normierungsinvariante der Utilities (mean ≈ 1.0)
- Plausibilitäts- und Stabilitätschecks (finite Werte)
- UTC-Anforderungen für `calculated_at`

## Anforderungen

Tests können mit Python's unittest-Modul (Standard-Bibliothek) oder mit pytest ausgeführt werden:

```bash
# Mit unittest (ohne zusätzliche Installation)
python -m unittest discover tests/

# Mit pytest (empfohlen, optional)
pip install pytest
python -m pytest tests/
```

## Hinweise

- Tests verwenden die echte Dreimetadaten API und sind daher von deren Verfügbarkeit abhängig
- API-Aufrufe können einige Sekunden dauern
- Bei Netzwerkproblemen können Tests fehlschlagen

# Tests

Dieser Ordner enthält automatisierte Tests für das Drei ??? Community Ranking Projekt.

## Struktur

Die Tests sind nach Modulen organisiert:
- `test_dreimetadaten_api.py` - Tests für das API-Wrapper-Modul

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

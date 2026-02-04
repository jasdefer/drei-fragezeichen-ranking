# Beispiele – Bradley-Terry-Modell

Dieses Verzeichnis enthält Beispielimplementierungen und Demonstrationen des Bradley-Terry-Modells.

## Dateien

### `bradley_terry_example.py`

Eine vollständige, ausführbare Demonstration des Bradley-Terry-Modells mit simulierten Daten.

**Funktionen**:
- Generiert realistische Dummy-Umfragen mit bekannten "wahren" Stärken
- Konvertiert aggregierte Stimmen zu paarweisen Vergleichen
- Berechnet Bradley-Terry-Ratings mit der `choix`-Bibliothek
- Zeigt die Ergebnisse an und vergleicht sie mit den wahren Stärken
- Demonstriert den Einfluss verschiedener Regularisierungsparameter

**Verwendung**:
```bash
# Installiere Abhängigkeiten
pip install choix numpy

# Führe das Beispiel aus
python examples/bradley_terry_example.py
```

**Ausgabe**:
- Konsolenausgabe mit Rankings und Vergleichen
- `example_ratings.tsv`: Beispieldatei im Format von `data/ratings.tsv`

### `example_ratings.tsv`

Beispielausgabe des Bradley-Terry-Modells mit Dummy-Daten.

**Format**: Identisch mit `data/ratings.tsv`
- `episode_id`: Folgen-ID
- `utility`: Normierte Stärke (Durchschnitt = 1.0)
- `matches`: Anzahl der Vergleiche, in denen die Folge beteiligt war
- `calculated_at`: Zeitstempel der Berechnung (ISO 8601, UTC)

## Verwendung als Referenz

Diese Beispiele können als Ausgangspunkt für die Implementierung der tatsächlichen Bradley-Terry-Berechnung im Projekt dienen:

1. **Datenaufbereitung**: Siehe `polls_to_comparisons()` für die Konvertierung von TSV-Daten
2. **Modellschätzung**: Siehe `compute_bradley_terry_ratings()` für die Verwendung von `choix`
3. **Ausgabeformat**: Siehe `save_example_output()` für das TSV-Ausgabeformat

## Weiterführende Informationen

- **Theoretische Grundlagen**: [../docs/bradley_terry_model.md](../docs/bradley_terry_model.md)
- **Datenschema**: [../docs/data_schema.md](../docs/data_schema.md)
- **choix Dokumentation**: https://choix.lum.li/

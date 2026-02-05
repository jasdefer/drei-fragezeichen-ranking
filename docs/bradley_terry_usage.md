# Bradley-Terry Rating-Berechnung

## Übersicht

Dieses Modul implementiert die Bradley-Terry-Rating-Berechnung auf Basis von paarweisen Vergleichsdaten aus `polls.tsv`.

## Verwendung

### Als Python-Modul

```python
from bot.bradley_terry import run_rating_update
from pathlib import Path

# Pfade zu den Daten
polls_path = Path("data/polls.tsv")
ratings_path = Path("data/ratings.tsv")

# Führe Rating-Update durch
run_rating_update(polls_path, ratings_path)
```

### Als Skript

```bash
python run_rating_update.py
```

## Funktionsweise

1. **Lädt finalisierte Polls** aus `polls.tsv`
   - Nur Polls mit `finalized_at <= jetzt (UTC)` werden verwendet
   - Polls mit 0 Stimmen werden geloggt und ignoriert

2. **Baut Konnektivitätsgraph** aller Episoden

3. **Filtert auf Episode 1**
   - Nur Episoden, die mit Episode 1 verbunden sind, werden gerankt
   - Andere Episoden werden geloggt und ignoriert

4. **Fittet Bradley-Terry-Modell**
   - MM-Algorithmus (Minorization-Maximization)
   - L2-Regularisierung mit `alpha = 0.01`
   - Verwendet `choix` Library

5. **Berechnet normierte Utilities**
   - Exponentialtransformation: `pi = exp(theta)`
   - Normierung: `utility = pi / mean(pi)` (arithmetisches Mittel = 1.0)

6. **Schreibt Ergebnisse** (append-only) in `ratings.tsv`
   - Format: `episode_id`, `utility`, `matches`, `calculated_at`
   - Alle Zeilen eines Laufs haben denselben `calculated_at` Timestamp

## Ausgabeformat

### ratings.tsv

```
episode_id	utility	matches	calculated_at
1	1.685657	4	2024-01-15T10:30:00Z
2	0.707837	3	2024-01-15T10:30:00Z
3	0.695777	4	2024-01-15T10:30:00Z
```

- **episode_id**: Externe Episoden-ID
- **utility**: Normierte Stärke (mean = 1.0)
  - Werte > 1.0: überdurchschnittlich beliebt
  - Werte < 1.0: unterdurchschnittlich beliebt
- **matches**: Anzahl der Vergleiche dieser Episode
- **calculated_at**: UTC-Timestamp der Berechnung (ISO-8601)

## Fehlerbehandlung

Das Modul wirft `BradleyTerryError` bei:
- Fehlenden/kaputten Spalten in `polls.tsv`
- Nicht parsebaren Zeitstempeln
- Fehlender Episode 1 im Vergleichsgraph
- Konvergenzfehlern im Modell

Warnings werden geloggt für:
- Polls mit 0 Stimmen
- Episoden, die nicht mit Episode 1 verbunden sind

## Tests

Führe Tests aus mit:

```bash
python -m unittest tests.test_bradley_terry -v
```

Alle 20 Tests sollten erfolgreich durchlaufen.

## Methodische Details

Siehe `docs/bradley_terry_research.md` für eine ausführliche Dokumentation der:
- Theoretischen Grundlagen
- Parameterwahl
- Regularisierung
- Normierung
- Literaturverweise

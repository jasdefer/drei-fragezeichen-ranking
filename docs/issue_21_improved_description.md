# Verbesserte Issue-Beschreibung für #21

Diese Datei enthält eine vorgeschlagene verbesserte Beschreibung für Issue #21, die direkt in GitHub kopiert werden kann.

---

Implementiere ein Skript (z.B. in Python), das mithilfe der Ergebnisse aus polls.tsv ein Bradley-Terry-Modell (Discrete Choice) ausführt und auf Basis der aktuellen Parameterisierung die ratings.tsv aktualisiert. Nutze nach Möglichkeit vorhandene Bibliotheken aus der Discrete Choice-/Statistik-Welt und dokumentiere Abweichungen von der in README beschriebenen Datenstruktur.

- Nutze die Bibliotheken und Parametrisierungen aus der Datei [docs/bradley_terry_research.md](https://github.com/jasdefer/drei-fragezeichen-ranking/blob/c752992b9ac90a57e6fc3141c5d9c538e4ac371b/docs/bradley_terry_research.md)
- Integration mit den bestehenden Datenformaten (episodes.tsv, polls.tsv, ratings.tsv)
- Automatisierbar via GitHub Action
- Klar dokumentieren, wie neue Ratings erzeugt werden

---

## Schnellreferenz: Kernparameter und Implementierung

### Bibliothek und Algorithmus
- **Bibliothek**: `choix==0.3.5` (Python)
- **Algorithmus**: MM (Minorization-Maximization) via `choix.opt_pairwise()`
- **Datenformat**: Binomial-Counts (w_ij, w_ji) pro Paar

### Modellparameter
- **Regularisierung**: L2 mit `alpha = 0.01`
- **Konvergenz**: `max_iter = 10000`, `tol = 1e-6`
- **Interner Constraint**: Σθ = 0 (geometric_mean(π) = 1) – wird automatisch von choix enforced
- **Ausgabe-Normierung**: mean(π) = 1 (arithmetisches Mittel) – Post-Processing nach Optimierung

### Input/Output-Spezifikation

**Input**: `data/polls.tsv`
- Nur finalisierte Polls (finalized_at ist gesetzt)
- Felder: poll_id, reddit_post_id, created_at, closes_at, episode_a_id, episode_b_id, votes_a, votes_b, finalized_at

**Output**: `data/ratings.tsv` (wird bei jeder Berechnung überschrieben)
- Spalten: `episode_id`, `strength`, `std_error`, `matches`
- `strength`: Normierte Stärke π_norm,i (Float, mean ≈ 1.0, 6 Dezimalstellen)
- `std_error`: Standardfehler (nullable, leer in Phase 1)
- `matches`: Anzahl Vergleiche dieser Folge (Integer)
- Sortierung: nach episode_id aufsteigend
- Header-Kommentar mit Methodik-Informationen

### Post-Processing
1. Exponentialtransformation: π_i = exp(θ_i)
2. Normierung auf arithmetisches Mittel: π_norm,i = π_i / mean(π)
3. Anzahl Matches pro Folge zählen
4. *(Optional in Phase 2)* Standardfehler via Bootstrap

---

## Akzeptanzkriterien

- [ ] Liest finalisierte Polls aus `data/polls.tsv`
- [ ] Verwendet `choix.opt_pairwise()` mit MM-Algorithmus
- [ ] Generiert `data/ratings.tsv` mit korrekten Spalten und Formatierung
- [ ] Normierung: mean(strength) ≈ 1.0 (Post-Processing nach Optimierung)
- [ ] Fehlerhandling für Randfälle:
  - Poll mit 0 Stimmen → Warnung, Poll ignorieren
  - Episode in polls, aber nicht in API → Fehler werfen
  - Vergleichsgraph nicht zusammenhängend → Warnung, nur größte Komponente ranken
  - Episode ohne Vergleiche → nicht in ratings.tsv
  - Numerische Konvergenzprobleme → Fehler loggen mit Details
- [ ] Unit-Tests mit synthetischen Daten (Korrelation > 0.95 zu wahren Stärken)
- [ ] Tests für alle Randfälle im Fehlerhandling
- [ ] CI-Integration mit Konnektivitäts-Check
- [ ] Dokumentation der finalen Parameter in README.md

---

## Referenzen zu bradley_terry_research.md

Für tiefergehende Details siehe:
- **Abschnitt 5**: Empfohlene Default-Parametrisierung (Tabelle)
- **Abschnitt 7**: Detaillierte Implementierungsspezifikation
  - 7.1: Input-Spezifikation
  - 7.2: Likelihood-Formulierung
  - 7.3: Algorithmus
  - 7.4: Post-Processing
  - 7.5: Output-Spezifikation
  - 7.6: Fehlerhandling
  - 7.7: Validierung & Tests

Für methodische Hintergründe siehe Abschnitte 1-4 des Recherche-Dokuments.

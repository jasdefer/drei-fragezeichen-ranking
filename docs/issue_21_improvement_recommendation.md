# Bewertung und Verbesserungsvorschlag für Issue #21

## Fragestellung

Ist das Issue #21 ausreichend gut beschrieben? Gerade mit der Beschreibung aus der verlinkten Datei zu der Parametrisierung?

## Bewertung der aktuellen Beschreibung

### Stärken
- ✅ Klares Ziel: Implementierung eines Bradley-Terry-Modell-Skripts
- ✅ Verweis auf umfassendes Recherche-Dokument (`bradley_terry_research.md`)
- ✅ Nennung der wichtigsten Anforderungen (Integration, Automation, Dokumentation)
- ✅ Klare Datenschnittstellen (polls.tsv → ratings.tsv)

### Verbesserungspotenzial

Die aktuelle Issue-Beschreibung ist **funktional, aber nicht optimal**. Hauptprobleme:

1. **Fehlende Schnellreferenz**: Implementierer müssen das 689-zeilige Recherche-Dokument vollständig lesen, um die Kernparameter zu finden
2. **Keine expliziten Akzeptanzkriterien**: Was genau muss implementiert werden, um das Issue als "erledigt" zu betrachten?
3. **Parametrisierung nicht direkt sichtbar**: Die Frage nach der Parametrisierung ist berechtigt – die konkreten Werte (α = 0.01, choix 0.3.5, etc.) sind nur im Recherche-Dokument zu finden

## Empfohlene Verbesserungen

### 1. Schnellreferenz für Kernparameter

Das Issue sollte eine kompakte Übersicht der wichtigsten Implementierungsdetails enthalten:

- **Bibliothek**: `choix==0.3.5` 
- **Algorithmus**: MM (Minorization-Maximization)
- **Regularisierung**: L2 mit `alpha = 0.01`
- **Konvergenz**: `max_iter = 10000`, `tol = 1e-6`
- **Ausgabe-Normierung**: mean(strength) = 1.0

Diese Information ist zwar im Recherche-Dokument (Abschnitt 5 & 7), sollte aber auch im Issue direkt verfügbar sein.

### 2. Explizite Akzeptanzkriterien

Eine Checkliste, was implementiert werden muss:
- Liest finalisierte Polls aus polls.tsv
- Verwendet choix mit den spezifizierten Parametern
- Generiert ratings.tsv mit korrektem Format
- Fehlerhandling für Randfälle
- Unit-Tests mit synthetischen Daten
- CI-Integration

### 3. Input/Output-Spezifikation

Konkrete Definition der Datenformate:
- **Input**: polls.tsv (welche Felder werden verwendet?)
- **Output**: ratings.tsv (Spalten: episode_id, strength, std_error, matches)
- Formatierung (6 Dezimalstellen, Sortierung, Header)

### 4. Strukturierte Referenzen

Klare Verweise auf relevante Abschnitte des Recherche-Dokuments:
- Abschnitt 5: Default-Parametrisierung
- Abschnitt 7: Implementierungsspezifikation
- Abschnitt 7.6: Fehlerhandling

## Vorgeschlagene verbesserte Issue-Beschreibung

Eine vollständige verbesserte Version ist als Markdown-Vorlage verfügbar:

```markdown
Implementiere ein Skript (z.B. in Python), das mithilfe der Ergebnisse aus polls.tsv ein Bradley-Terry-Modell (Discrete Choice) ausführt und auf Basis der aktuellen Parameterisierung die ratings.tsv aktualisiert. Nutze nach Möglichkeit vorhandene Bibliotheken aus der Discrete Choice-/Statistik-Welt und dokumentiere Abweichungen von der in README beschriebenen Datenstruktur.

- Nutze die Bibliotheken und Parametrisierungen aus der Datei [docs/bradley_terry_research.md](...)
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
```

## Fazit

**Antwort auf die Ausgangsfrage**: Das Issue #21 ist **grundsätzlich ausreichend, aber verbesserungswürdig**. 

Die Verlinkung zum Recherche-Dokument ist korrekt und das Dokument selbst ist exzellent. Jedoch:

1. **Parametrisierung ist gut dokumentiert** (im Recherche-Dokument) ✅
2. **Parametrisierung ist nicht direkt im Issue sichtbar** ❌
3. **Implementierer müssen erst suchen** (689 Zeilen durchforsten) ❌

**Empfehlung**: Issue-Beschreibung um Schnellreferenz, Akzeptanzkriterien und strukturierte Verweise ergänzen. Dies macht das Issue actionable, ohne die Qualität des Recherche-Dokuments zu duplizieren.

## Nächste Schritte

1. ✅ Diese Analyse wurde dokumentiert
2. ⏭️ Issue #21 mit der vorgeschlagenen Beschreibung aktualisieren
3. ⏭️ Alternativ: Dieses Dokument als Grundlage für Diskussion nutzen

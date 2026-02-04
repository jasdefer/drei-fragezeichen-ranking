# Bradley-Terry-Modell: Recherche und Parametrisierung

Dieses Dokument fasst die Recherche zu Bradley-Terry-Modellen und Discrete Choice Methoden für die Auswertung paarweiser Vergleiche zusammen. Es dient als Diskussionsgrundlage für die Festlegung der Modellparametrisierung und als Spezifikation für die spätere Implementierung.

---

## Inhaltsverzeichnis

1. [Problemstellung](#problemstellung)
2. [Theoretische Grundlagen](#theoretische-grundlagen)
3. [Stand der Praxis in Verhaltensumfragen](#stand-der-praxis-in-verhaltensumfragen)
4. [Verfügbare Ansätze und Bibliotheken](#verfügbare-ansätze-und-bibliotheken)
5. [Zu diskutierende Parametrisierungen](#zu-diskutierende-parametrisierungen)
6. [Empfohlene Default-Parametrisierung](#empfohlene-default-parametrisierung)
7. [Spezifikation für Implementierung](#spezifikation-für-implementierung)
8. [Offene Fragen und Entscheidungen](#offene-fragen-und-entscheidungen)
9. [Literatur und Referenzen](#literatur-und-referenzen)

---

## Problemstellung

Wir sammeln paarweise Vergleichsdaten über Reddit-Polls („Folge A vs. Folge B"). Aus diesen aggregierten Abstimmungsergebnissen möchten wir ein Ranking aller Folgen ableiten.

**Anforderungen:**
- Umgang mit aggregierten Stimmdaten (z.B. 65 vs. 35 Stimmen)
- Umgang mit unvollständigen Vergleichen (nicht jede Folge wird mit jeder verglichen)
- Stabile Schätzungen auch bei wenigen Vergleichen pro Folge
- Nachvollziehbare, interpretierbare Ergebnisse mit **Unsicherheitsmaßen**
- Transparente, reproduzierbare Methodik

---

## Theoretische Grundlagen

### Das Bradley-Terry-Modell

**Ursprung**: Bradley & Terry (1952) – „Rank Analysis of Incomplete Block Designs"

**Grundidee**: Jedes Element (hier: Folge) besitzt eine latente **Stärke** π_i (oder im Log-Space: θ_i = log π_i). Die Wahrscheinlichkeit, dass Element i gegenüber Element j bevorzugt wird, ist:

```
P(i > j) = π_i / (π_i + π_j) = σ(θ_i - θ_j)
```

wobei σ(x) = 1/(1 + exp(-x)) die logistische Funktion ist.

**Verbindung zu Logit-Modellen**:
```
log(P(i > j) / P(j > i)) = log(π_i / π_j) = θ_i - θ_j
```

Dies ist äquivalent zu einem **konditionalen Logit-Modell**, einem Standardwerkzeug in der Discrete Choice Analyse.

### Einordnung in Discrete Choice

Das Bradley-Terry-Modell ist ein Spezialfall von:
- **Luce's Choice Axiom** (1959): Rational Choice aus endlichen Alternativen
- **Konditionalen Logit-Modellen** (McFadden, 1974): Diskrete Wahlentscheidungen
- **Item Response Theory** (IRT): In der Psychometrie für Paarvergleiche

**Wichtige Eigenschaften:**

1. **Independence of Irrelevant Alternatives (IIA)**:
   - Bei Paarvergleichen ist IIA weniger problematisch als bei Multinomial-Logit über viele Alternativen
   - Relevant wird IIA erst bei Verallgemeinerung auf Plackett-Luce (Rankings über > 2 Alternativen)
   - Für unseren Paarvergleichs-Fall: Die logistische Form ist eine natürliche Annahme

2. **Transitivität und Zyklen**:
   - **Wichtige Klarstellung**: Das BT-Modell selbst ist transitiv in den latenten Stärken
   - Wenn θ_A > θ_B und θ_B > θ_C, dann gilt im Modell auch P(A > C) > 0.5
   - **Daten können intransitiv sein** (Individuen/Gruppen zeigen Zyklen A > B > C > A)
   - BT liefert eine **best-fit eindimensionale Rangordnung** trotz potentiell intransitiver Daten
   - Das Modell kann Zyklen in den Daten "sehen", aber die geschätzten Stärken sind immer transitiv

3. **Identifizierbarkeit**:
   - Nur **relative Stärken** sind identifizierbar, nicht absolute Werte
   - **Skalenfixierung notwendig**: z.B. ∑ θ_i = 0 oder mean(π) = 1
   - Interpretation über **Differenzen**: Δθ = θ_i - θ_j ist der Log-Odds
   - Win-Probability: P(i > j) = σ(θ_i - θ_j)

---

## Stand der Praxis in Verhaltensumfragen

### Typische Anwendungen

**1. Marketing und Präferenzforschung (Conjoint Analysis)**
- Produktvergleiche: „Welches Produkt würden Sie kaufen?"
- Oft mit Zusatzinformationen (Preis, Features)
- Typische Stichproben: 100-1000 Probanden, 10-50 Produkte

**2. Sportstatistik (Rankings)**
- Elo-Rating (Schach, eSports)
- TrueSkill (Microsoft, Xbox Live)
- Erweiterungen des Bradley-Terry für zeitliche Dynamik

**3. Psychologische Tests und Bewertungen**
- Personality Assessment (Forced Choice)
- Präferenzstudien in der Verhaltensforschung
- Oft mit hierarchischen Modellen (Unterschiede zwischen Personen)

### Gängige Praxis bei der Parametrisierung

**Regularisierung:**
- **Problem**: Bei wenigen Vergleichen können MLE-Schätzer instabil werden oder divergieren
- **Lösung in der Praxis**: 
  - **L2-Regularisierung (Ridge)**: Shrinkage zum Mittelwert (nicht "Bias towards 0")
  - Entspricht einem **weakly-informative Normal-Prior** auf θ_i
  - Bayesianische Interpretation: Prior-Varianz σ²_prior = 1/α
  - Typische Werte: Schwache Regularisierung (α = 0.001 - 0.1)

**Wahl von α:**
- **Cross-Validation**: Hold-out Polls zum Testen der Vorhersagekraft
- **Empirical Bayes**: Schätzung der Prior-Varianz aus Daten
- **Zielmetrik**: Trade-off zwischen Stabilität (wenige Daten) und Reaktionsfähigkeit (viele Daten)

**Umgang mit aggregierten Daten:**

**Wichtige Klarstellung**: Für Bradley-Terry sind folgende Ansätze **mathematisch äquivalent**, sofern die Likelihood korrekt formuliert wird:

- **Binomial-Form** (bevorzugt): 
  - Ein Poll liefert w_ij Stimmen für i über j und w_ji Stimmen umgekehrt
  - Log-Likelihood: w_ij · log P(i > j) + w_ji · log P(j > i)
  - ✅ Effizient, sauber, direkt interpretierbar

- **Disaggregierung**: 
  - Expansion: 65 Stimmen für i → 65 Einträge (i beats j)
  - ❌ Unnötig teuer (große Datenmengen)
  - Funktioniert, aber keine Vorteile gegenüber Binomial-Form

**Empfehlung**: **Binomial-Counts (w_ij, w_ji) pro Paar**, nicht Expansion.

**Startwerte:**
- Standard: Gleichverteilte Startwerte (θ_i = 0 für alle Folgen)
- Alternative: Initiale Schätzungen aus Win-Rate (optional, meist nicht nötig)

**Konvergenzkriterien:**
- Toleranz für Parameteränderungen: typisch 1e-6 bis 1e-8
- Maximale Iterationen: 1000-10000
- In der Praxis: Konvergenz nach 100-500 Iterationen bei gut-konditionierten Problemen

**Unsicherheitsquantifizierung:**
- **Standardfehler** über Bootstrap (resampling über Polls)
- Alternative: Hesse-Matrix / Fisher Information (erfordert eigene Implementierung)
- Für Community wichtig: Nicht nur Rang, sondern auch **"Bandbreite"** / Konfidenzintervall
- Kennzeichnung: „Unsicher, weil erst 2 Matches"

---

## Verfügbare Ansätze und Bibliotheken

### 1. choix (Python) – **Empfohlen**

**Repository**: https://github.com/lucasmaystre/choix  
**Entwickler**: Lucas Maystre (EPFL)  
**Status**: Aktiv gewartet, wissenschaftlich fundiert

**Funktionen:**
- **MM (Minorization-Maximization)**: Garantierte Konvergenz, klassisch robust
- **ILSR (Iterative Luce Spectral Ranking)**: Schneller Initializer
- **Rank Centrality**: Spektraler Ansatz (nur als Baseline/Debug, nicht als Hauptschätzung)
- Unterstützt L2-Regularisierung
- Verschiedene Datenformate: Paarvergleiche, Rankings, Top-k

**Algorithmus-Empfehlung**:
- **Hauptschätzung: MM** (sicher konvergierend, robust)
- **Schnelle Initialisierung: ILSR** (optional)
- **Nicht für finale Schätzung: Rank Centrality** (nur Debug/Baseline)

**Verwendung in der Forschung:**
- Publikationen in NIPS, ICML, JMLR
- Verwendet in akademischen Studien zu Crowd-Sourced Rankings

**Vorteile für unser Projekt:**
- Spezialisiert auf Paarvergleiche
- Gut dokumentiert
- Einfache API
- Wissenschaftlich validiert
- **Akzeptiert direkt Binomial-Counts (wins, losses)**

**Nachteile:**
- Keine dynamischen/zeitabhängigen Modelle
- Keine hierarchischen Modelle (individuelle Unterschiede)
- **Keine Hesse-Matrix / Standardfehler-Ausgabe** (Bootstrap notwendig)

### 2. scipy.optimize (Python)

**Ansatz**: Eigene Implementierung der Log-Likelihood mit scipy's Optimierern

**Vorteile:**
- Volle Kontrolle über Modell und Parametrisierung
- Keine zusätzlichen Abhängigkeiten
- Erweiterbar für komplexere Modelle

**Nachteile:**
- Mehr Implementierungsaufwand
- Numerische Stabilität muss selbst sichergestellt werden
- Weniger getestet als spezialisierte Bibliotheken

### 3. BradleyTerry2 (R)

**Paket**: BradleyTerry2 (R)  
**Status**: Gold-Standard in der R-Community, sehr ausgereift

**Funktionen:**
- Umfangreiche Modelldiagnostik
- Erweiterungen für Tie-Gleichstände, Home-Advantage
- Sehr gut dokumentiert mit Vignettes

**Vorteile:**
- Gold-Standard in der Statistik-Community
- Exzellente Dokumentation
- Viele Erweiterungen

**Nachteile:**
- Benötigt R statt Python
- Integration in GitHub Actions komplexer

### 4. Weitere Optionen

**PyMC / Stan (Bayesianisch):**
- Volle Bayesianische Inferenz mit MCMC
- Sehr flexibel, aber komplexer und rechenintensiv
- Für unseren Use-Case vermutlich Overkill

---

## Zu diskutierende Parametrisierungen

### 1. Regularisierung

**Option A: Keine Regularisierung (Pure MLE)**
- ✅ Theoretisch optimal bei ausreichend Daten
- ❌ Instabil bei wenigen Vergleichen
- ❌ Neue Folgen mit 1-2 Vergleichen problematisch

**Option B: L2-Regularisierung (Ridge) – EMPFOHLEN**
- ✅ Stabilisiert Schätzungen
- ✅ Verhindert extreme Werte
- ✅ Interpretierbar als weakly-informative Normal-Prior
- ❓ **Wie stark? α = 0.001, 0.01, 0.1?**

**Entscheidungskriterium für α:**
- **Cross-Validation** mit Hold-out Polls
- **Empirical Bayes**: Schätzung aus Daten
- **Trade-off**: Stabilität vs. Reaktionsfähigkeit

**Option C: Bayesianischer Prior (PyMC/Stan)**
- ✅ Theoretisch fundiert
- ✅ Flexibel, mit Unsicherheitsquantifizierung
- ❌ Komplexer, rechenintensiv
- ❌ Schwerer zu erklären

**Frage zur Diskussion:**
- Welche Regularisierung ist für unseren Use-Case sinnvoll?
- Wie wird α gewählt (CV, fixed, adaptive)?
- Sollen wir adaptive Strategien erwägen (stärkere Regularisierung für Folgen mit wenigen Vergleichen)?

### 2. Datenformat

**Option A: Binomial-Counts (EMPFOHLEN)**
- Ein Poll liefert (w_ij, w_ji) = (Stimmen für i, Stimmen für j)
- ✅ Effizient
- ✅ Mathematisch sauber
- ✅ Direkt von choix und anderen Libraries unterstützt

**Option B: Disaggregierung (nicht empfohlen)**
- 65 Stimmen für A → 65 Einträge (A beats B)
- ❌ Unnötig große Datenmengen
- ❌ Keine Vorteile gegenüber Binomial-Form

**Entscheidung**: **Binomial-Form** verwenden.

### 3. Identifizierbarkeits-Constraint (Skalenfixierung)

**Notwendig**, da nur relative Stärken identifizierbar sind.

**Interner Constraint vs. Ausgabe-Normierung:**

Der Optimierungsalgorithmus (choix) verwendet intern:
- **∑ θ_i = 0** (Log-Space)
- Dies entspricht: **geometric_mean(π) = 1**

Für die Ausgabe transformieren wir zu:
- **mean(π) = 1** (arithmetisches Mittel)
- Dies ist ein **Post-Processing-Schritt** nach der Optimierung

**Warum diese Trennung?**
- Interner Constraint (∑ θ = 0) ist numerisch stabil und Standard in choix
- Ausgabe-Normierung (mean(π) = 1) ist intuitiver für die Community

**Interpretation:**
- π_i > 1: überdurchschnittliche Präferenzstärke
- π_i < 1: unterdurchschnittliche Präferenzstärke
- π_i = 1: exakt durchschnittlich

### 4. Ausgabeformat

**Option A: Log-Stärken (θ_i = log π_i)**
- Natürliche Parameterdarstellung
- ❌ Schwer zu interpretieren (negative Werte, keine klare Skala)

**Option B: Rohe Stärken (π_i)**
- ✅ Positive Werte
- ❌ Absolute Skala willkürlich ohne Normierung

**Option C: Normierte Stärken (π_i / mean(π)) – EMPFOHLEN**
- ✅ Durchschnitt = 1.0
- ✅ Werte > 1: überdurchschnittlich, < 1: unterdurchschnittlich
- ✅ Gut interpretierbar für Community

**Option D: Win-Probabilities gegen Durchschnittsfolge**
- P(i beats avg) = π_norm,i / (π_norm,i + 1)
- ✅ Intuitive Interpretation (Prozent)
- ✅ Als Zusatzausgabe sinnvoll
- ⚠️ **Wichtig**: Dies ist die Gewinnwahrscheinlichkeit gegen eine **hypothetische Folge mit Stärke 1.0**, nicht gegen eine zufällig gewählte Folge

**Empfehlung**: **Normierte Stärken (π_i / mean(π))** als Hauptausgabe, Win-Probabilities als Zusatz.

**Spaltenname**: `strength` statt `utility` – intuitiver für die Community und vermeidet Verwechslung mit klassischen Nutzenwerten aus der Ökonomie.

### 5. Umgang mit unvollständigen Daten

**Bedingung für BT**: Der Vergleichsgraph muss **(schwach) zusammenhängend** sein.
- D.h.: Jede Folge muss über eine Kette von Vergleichen mit jeder anderen verbunden sein
- Sonst gibt es getrennte Skalen / nicht vergleichbare Komponenten

**Praktische Maßnahmen:**

1. **Monitoring im CI**:
   - Warnung, wenn neue Episode noch nicht mit Hauptgraph verbunden ist
   - Check: Graph-Konnektivität vor jeder Bradley-Terry-Berechnung

2. **Matchmaking-Regeln**:
   - Neue Folgen bekommen gezielt "Brücken"-Matches
   - Empfehlung: Neue Folgen gegen bereits gerankte Folgen paaren
   - Optional: Adaptive Paarung (ähnliche geschätzte Stärken für informativere Vergleiche)

3. **Umgang mit isolierten Folgen**:
   - Separate Liste "unranked" für Folgen ohne Vergleiche
   - Markierung: "Noch nicht genug Daten"

### 6. Umgang mit Tie-Gleichständen

**Saubere Formulierung**: Ein Poll liefert w_ij und w_ji als Binomial/Multinomial-Outcome.

- Ein 50:50-Ergebnis ist **informativ** (spricht für ähnliche Stärke)
- Keine Sonderbehandlung nötig
- Likelihood: w_ij · log P(i > j) + w_ji · log P(j > i)

**Fazit**: Keine speziellen Tie-Modelle nötig. Die Binomial-Form behandelt alle Fälle konsistent.

### 7. Zeitliche Dynamik

**Option A: Statisches Modell – EMPFOHLEN FÜR START**
- Alle Daten werden gleich gewichtet
- ✅ Einfach, nachvollziehbar
- ✅ Für erste 1-2 Jahre ausreichend
- ❌ Frühe Votes haben gleiche Gewichtung wie späte

**Option B: Zeitabhängiges Modell (später optional)**
- Ältere Votes werden weniger gewichtet (exponentielles Decay)
- ✅ Reflektiert Änderungen in Präferenzen
- ❌ Komplexer
- ❓ Wie stark Decay? (Halbwertszeit: 1 Jahr, 6 Monate?)

**Option C: Elo-ähnliches Update-System**
- Stärken werden nach jedem Poll aktualisiert
- ✅ Sehr dynamisch
- ❌ Schwerer nachvollziehbar
- ❌ Keine historische Konsistenz

**Empfehlung**: 
- **Zunächst statisches Modell**
- Bei Bedarf später auf zeitgewichtetes Modell erweitern
- Klar dokumentieren, falls Methodik geändert wird

**Begründung**: 
- Folgen sind statisch (ändern sich nicht)
- Präferenzen ändern sich vermutlich langsam
- Hauptdrift ist eher Sampling als echte Präferenzänderung

### 8. Versionierung und Historie

**Ansatz: Git-basierte Versionierung statt Append-Only**

Statt einer append-only Datei mit Timestamps nutzen wir die **Git-History** für die Historisierung:

- `ratings.tsv` enthält **nur den aktuellen Stand** (wird bei jeder Berechnung überschrieben)
- Jeder Commit dokumentiert den Zeitpunkt und die verwendeten Daten
- Historische Werte sind über `git log` / `git show` abrufbar

**Vorteile:**
- ✅ Datei bleibt kompakt (n_episodes Zeilen, nicht n_episodes × n_runs)
- ✅ Konsistent mit Projektphilosophie "vollständige Historie über Git"
- ✅ Keine redundante Datenhaltung
- ✅ Diff-freundlich: Änderungen pro Folge direkt sichtbar

**Commit-Konvention:**
```
chore(ratings): Update ratings after poll #42

Polls processed: 42
Episodes ranked: 87
Mean strength: 1.000000
```

**Optionale Erweiterung (später):**
- Separates `ratings_history.tsv` für explizite Zeitreihen-Analysen
- Nur bei konkretem Bedarf (z.B. Trend-Visualisierung)

---

## Empfohlene Default-Parametrisierung

Basierend auf obiger Diskussion wird folgende **Default-Parametrisierung** empfohlen:

| Parameter | Empfohlener Wert | Begründung |
|-----------|------------------|------------|
| **Modell** | Bradley-Terry (logistische Paarwahl) | Standard für Paarvergleiche |
| **Bibliothek** | choix (Python) | Spezialisiert, wissenschaftlich validiert |
| **Algorithmus** | MM (Minorization-Maximization) | Garantierte Konvergenz, robust |
| **Datenformat** | Binomial-Counts (w_ij, w_ji) | Effizient, mathematisch sauber |
| **Regularisierung** | L2 mit **α = 0.01** (initial) | Schwache Regularisierung, später per CV anpassen |
| **Interner Constraint** | ∑ θ_i = 0 (geometric_mean(π) = 1) | Standard in choix, numerisch stabil |
| **Ausgabe-Normierung** | mean(π) = 1 (arithmetisches Mittel) | Intuitiv interpretierbar |
| **Ausgabeformat** | Normierte Stärken als `strength` | Durchschnitt = 1.0, intuitive Interpretation |
| **Zusatzausgabe** | Win-Prob vs. Durchschnittsfolge: π_i / (π_i + 1) | Prozent-Interpretation |
| **Unsicherheit** | Bootstrap (Phase 2) | choix liefert keine Hesse-Matrix |
| **Konvergenz** | tol = 1e-6, max_iter = 10000 | Standard, ausreichend genau |
| **Zeitdynamik** | Statisch (zunächst) | Einfach, später erweiterbar |
| **Versionierung** | Git-History (nicht append-only) | Kompakt, konsistent mit Projektphilosophie |
| **Konnektivitäts-Check** | Warnung bei isolierten Folgen | Sicherstellen, dass Graph zusammenhängend |

**Anpassungen nach ersten Daten:**
- α über Cross-Validation optimieren
- Bootstrap für Unsicherheitsmaße implementieren (nach 20-30 Polls)
- Bei Bedarf: Zeitgewichtung hinzufügen

---

## Spezifikation für Implementierung

Dieser Abschnitt definiert konkrete Anforderungen für die Implementierung (Child Issue).

### 1. Input-Spezifikation

**Quelle**: `data/polls.tsv`

**Format**:
```
poll_id	reddit_post_id	created_at	closes_at	episode_a_id	episode_b_id	votes_a	votes_b	finalized_at
1	abc123	2024-01-15T10:00:00Z	2024-01-22T10:00:00Z	1	5	42	38	2024-01-22T11:30:00Z
```

**Verarbeitung**:
- Nur finalized Polls (finalized_at ist gesetzt)
- Validierung: votes_a, votes_b ≥ 0
- Validierung: episode_a_id ≠ episode_b_id
- Validierung: episode_a_id, episode_b_id existieren in episodes (aus API)

### 2. Likelihood-Formulierung

**Binomial-Form** pro Poll zwischen Folgen i und j:

```
L(θ) = ∏ P(i > j)^w_ij · P(j > i)^w_ji
```

mit P(i > j) = exp(θ_i) / (exp(θ_i) + exp(θ_j)) = σ(θ_i - θ_j)

**Log-Likelihood mit L2-Regularisierung**:

```
ℓ(θ) = ∑ [w_ij · log P(i > j) + w_ji · log P(j > i)] - (α/2) · ∑ θ_i²
```

**Interner Constraint**: ∑ θ_i = 0 (wird von choix automatisch enforced)

### 3. Algorithmus

**Verwendung**: `choix.opt_pairwise()` mit MM-Algorithmus

**Parameter**:
- `alpha = 0.01` (L2-Regularisierung)
- `max_iter = 10000`
- `tol = 1e-6`

**Ausgabe**: θ_i (Log-Stärken) für alle Folgen im zusammenhängenden Graph

### 4. Post-Processing

**Schritte**:
1. Exponentialtransformation: π_i = exp(θ_i)
2. Normierung auf arithmetisches Mittel: π_norm,i = π_i / mean(π)
3. Win-Probability vs. Durchschnittsfolge: p_i = π_norm,i / (π_norm,i + 1)
4. Anzahl Matches pro Folge zählen
5. *(Phase 2)* Standardfehler via Bootstrap

**Hinweis zur Normierung**:
- choix liefert θ mit ∑ θ = 0, d.h. geometric_mean(π) = 1
- Wir renormieren auf arithmetic_mean(π) = 1 für intuitivere Interpretation
- Differenz ist gering, aber Konsistenz in der Dokumentation wichtig

### 5. Output-Spezifikation

**Datei**: `data/ratings.tsv` (wird bei jeder Berechnung überschrieben)

**Format**:
```
episode_id	strength	std_error	matches
1	1.234500	0.023400	5
5	0.876500	0.018900	5
```

**Spalten**:
- `episode_id`: Folgen-ID (Integer)
- `strength`: Normierte Stärke π_norm,i (Float, mean ≈ 1.0)
- `std_error`: Standardfehler (Float, nullable – leer in Phase 1)
- `matches`: Anzahl Vergleiche dieser Folge (Integer)

**Formatierung**:
- Floats: 6 Dezimalstellen
- Sortierung: nach episode_id aufsteigend
- Encoding: UTF-8
- Zeilenenden: LF (Unix-Style)

**Header-Kommentar**:
```
# Bradley-Terry Ratings
# Method: choix MM, L2 regularization (alpha=0.01)
# Normalization: mean(strength) = 1.0
# Columns: episode_id, strength, std_error, matches
episode_id	strength	std_error	matches
```

**Versionierung**:
- Datei wird bei jedem Lauf überschrieben
- Historie über Git-Commits verfügbar
- Commit-Message enthält Metadaten (Anzahl Polls, Episodes)

### 6. Fehlerhandling

**Randfälle**:

| Fall | Behandlung |
|------|------------|
| **Poll mit 0 Stimmen** | Warnung loggen, Poll ignorieren |
| **Episode in polls, aber nicht in API** | Fehler werfen, Abbruch |
| **Vergleichsgraph nicht zusammenhängend** | Warnung loggen, nur größte Komponente ranken, Rest in "unranked" |
| **Episode ohne Vergleiche** | In separate Liste "unranked", nicht in ratings.tsv |
| **Numerische Konvergenzprobleme** | Fehler loggen mit Details, Abbruch (nicht still ignorieren) |
| **Keine finalisierten Polls** | Warnung loggen, leere ratings.tsv (nur Header) |

### 7. Validierung & Tests

**Vor Deployment**:
- Unit-Tests mit synthetischen Daten (bekannte wahre Stärken)
- Test: Korrelation zwischen geschätzten und wahren Stärken > 0.95
- Test: Konnektivitäts-Check funktioniert
- Test: Fehlerhandling für alle Randfälle
- Test: Normierung korrekt (mean(strength) ≈ 1.0)

**Im CI**:
- Konnektivitäts-Check vor jeder Berechnung
- Warnung, falls neue Folge nicht verbunden
- Plausibilitäts-Checks: mean(strength) ≈ 1.0, std(strength) > 0

### 8. Reproduzierbarkeit

**Anforderungen**:
- Fixe Python-Version (z.B. 3.11)
- Pinned dependencies in `requirements.txt`:
  - `choix==0.3.5`
  - `numpy==1.24.0` (oder kompatibel)
- Deterministische Ausgabe:
  - Sortierung: nach episode_id
  - Float-Formatierung: 6 Dezimalstellen
- Keine Zufallskomponenten im Algorithmus (MM ist deterministisch)

### 9. Dokumentation

**In README.md ergänzen**:
- Abschnitt "Berechnungsmethodik"
- Verweis auf dieses Dokument (bradley_terry_research.md)
- Finale Parameter explizit auflisten:
  - Modell: Bradley-Terry
  - Regularisierung: L2 mit α = 0.01
  - Ausgabeformat: Normierte Stärken (mean = 1.0)
  - Bibliothek: choix 0.3.5
  - Algorithmus: MM

---

## Phasenplan für Implementierung

### Phase 1: MVP (Initiale Implementierung)

**Ziel**: Funktionierendes Ranking ohne Unsicherheitsmaße

**Umfang**:
- Grundlegende Bradley-Terry-Berechnung mit choix
- Normierte Stärken (`strength`) als Ausgabe
- `std_error` Spalte vorhanden, aber leer (Platzhalter)
- Konnektivitäts-Check
- Basis-Fehlerhandling

**Meilenstein**: Erste echte Berechnung nach 10-15 Polls

### Phase 2: Unsicherheitsquantifizierung (nach 20-30 Polls)

**Ziel**: Bootstrap-basierte Standardfehler

**Umfang**:
- Bootstrap-Resampling über Polls (nicht über Stimmen)
- Konfidenzintervalle für jede Folge
- Visualisierung der Unsicherheit auf GitHub Pages

**Begründung für Verzögerung**:
- Bootstrap benötigt ausreichend Polls für stabile Schätzungen
- choix liefert keine native Hesse-Matrix
- Priorität liegt zunächst auf funktionierendem Ranking

### Phase 3: Optimierung (nach 100+ Polls)

**Ziel**: Feintuning der Modellparameter

**Umfang**:
- Cross-Validation für optimales α
- Evaluation: Sind Standardfehler plausibel?
- Optional: Adaptive Matchmaking-Vorschläge
- Optional: Ankerfolge für stabile Langzeit-Vergleiche

---

## Offene Fragen und Entscheidungen

### Methodische Fragen

1. **Regularisierung α**:
   - Start mit α = 0.01
   - **TODO**: Nach ersten 50-100 Polls Cross-Validation durchführen
   - Optimales α per Grid-Search oder Empirical Bayes?

2. **Bootstrap-Details** (Phase 2):
   - Anzahl Resamples: 1000? 5000?
   - Resampling-Einheit: Polls (empfohlen) oder Stimmen?
   - Konfidenzintervall: 95%? Perzentil-Methode?

3. **Adaptive Matchmaking**:
   - Sollen zukünftige Polls gezielt informative Paarungen vorschlagen?
   - Z.B. Folgen mit ähnlichen geschätzten Stärken paaren?
   - **TODO**: Nach stabilem Ranking diskutieren

4. **Zeitgewichtung**:
   - Wann ist zeitgewichtetes Modell sinnvoll?
   - **TODO**: Nach 1-2 Jahren evaluieren, ob Präferenzen driften

5. **Ankerfolge für Langzeit-Stabilität**:
   - Bei `mean(π) = 1` verschieben sich alle Werte, wenn neue Folgen hinzukommen
   - Alternative: Eine Referenzfolge auf π = 1.0 fixieren
   - **TODO**: Evaluieren nach 100+ Polls, ob Drift problematisch ist

### Technische Fragen

6. **Bibliothek**:
   - choix als Default?
   - Fallback auf scipy bei Problemen?
   - **Entscheidung**: choix verwenden, scipy als Backup dokumentieren

7. **Performance**:
   - Wie skaliert choix MM bei 100, 500, 1000 Folgen?
   - **TODO**: Benchmark mit simulierten Daten

8. **CI-Integration**:
   - GitHub Actions Workflow für automatische Berechnung?
   - Trigger: Neue finalisierte Polls in polls.tsv?
   - **TODO**: Nach Implementierung CI-Setup

### Kommunikation & Visualisierung

9. **Community-Präsentation**:
   - Nur Rangliste oder mit Unsicherheitsbändern?
   - Zusätzlich: Win-Probability-Tabellen?
   - **TODO**: Mock-up erstellen

10. **Changelog**:
    - Wie kommunizieren wir Parameteränderungen?
    - Separate CHANGELOG.md für Methodik?
    - **TODO**: Format definieren

11. **Trend-Visualisierung**:
    - Historie der Stärken über Zeit anzeigen?
    - Welche Folgen steigen/fallen?
    - **TODO**: Nach Daten-Akkumulation umsetzen (Git-History nutzen)

---

## Literatur und Referenzen

### Grundlagenwerke

**Bradley-Terry-Modell:**
1. Bradley, R. A., & Terry, M. E. (1952). *Rank Analysis of Incomplete Block Designs: I. The Method of Paired Comparisons*. Biometrika, 39(3/4), 324-345.

2. Hunter, D. R. (2004). *MM algorithms for generalized Bradley-Terry models*. The Annals of Statistics, 32(1), 384-406.
   - Grundlage für den MM-Algorithmus in choix

**Discrete Choice:**
3. Luce, R. D. (1959). *Individual Choice Behavior: A Theoretical Analysis*. Wiley.
   - Luce's Choice Axiom als theoretische Basis

4. McFadden, D. (1974). *Conditional logit analysis of qualitative choice behavior*. In P. Zarembka (Ed.), Frontiers in Econometrics (pp. 105-142).
   - Verbindung zu Logit-Modellen

5. Train, K. E. (2009). *Discrete Choice Methods with Simulation* (2nd ed.). Cambridge University Press.
   - Umfassendes Lehrbuch

### Praktische Anwendungen

6. Glickman, M. E. (1999). *Parameter estimation in large dynamic paired comparison experiments*. Journal of the Royal Statistical Society: Series C, 48(3), 377-394.
   - Zeitabhängige Bradley-Terry-Modelle

7. Cattelan, M. (2012). *Models for paired comparison data: A review with emphasis on dependent data*. Statistical Science, 27(3), 412-433.
   - Umfassende Übersicht über Erweiterungen

8. Maystre, L., & Grossglauser, M. (2015). *Fast and Accurate Inference of Plackett-Luce Models*. NIPS 2015.
   - Grundlage der choix-Bibliothek, ILSR-Algorithmus

### Software und Tools

9. Maystre, L. (2018). *choix: Inference algorithms for models based on Luce's choice axiom*.
   - https://github.com/lucasmaystre/choix
   - Dokumentation: https://choix.lum.li/

10. Turner, H., & Firth, D. (2012). *Bradley-Terry Models in R: The BradleyTerry2 Package*. Journal of Statistical Software, 48(9).
    - R-Referenzimplementierung

### Verhaltensforschung und Umfragen

11. Louviere, J. J., Hensher, D. A., & Swait, J. D. (2000). *Stated Choice Methods: Analysis and Applications*. Cambridge University Press.
    - Discrete Choice in Survey Design

12. Agresti, A. (2013). *Categorical Data Analysis* (3rd ed.). Wiley.
    - Statistischer Hintergrund, binomiale Modelle

---

## Zusammenfassung und nächste Schritte

### Was bereits festgelegt ist

✅ **Modell**: Bradley-Terry (logistische Paarwahl)  
✅ **Bibliothek**: choix (Python)  
✅ **Algorithmus**: MM (Minorization-Maximization)  
✅ **Datenformat**: Binomial-Counts (w_ij, w_ji)  
✅ **Regularisierung**: L2 mit α = 0.01 (initial)  
✅ **Interner Constraint**: ∑ θ = 0 (geometric_mean(π) = 1)  
✅ **Ausgabe-Normierung**: mean(π) = 1 (arithmetisches Mittel)  
✅ **Ausgabeformat**: Normierte Stärken als `strength`  
✅ **Versionierung**: Git-History (nicht append-only)  
✅ **Workflow**: polls.tsv → Fit → ratings.tsv (überschreibend)

### Was noch zu diskutieren ist

❓ Finale Bestätigung der Default-Parametrisierung  
❓ Details der Bootstrap-Implementierung (Phase 2)  
❓ Visualisierung und Community-Präsentation  
❓ Langfristig: Adaptive Matchmaking, Zeitgewichtung, Ankerfolge

### Nächste Schritte

1. **Diskussion und Finalisierung** dieses Dokuments
2. **Phase 1 implementieren**: MVP ohne Standardfehler
3. **Validierung** mit synthetischen Daten
4. **Erste reale Berechnung** nach 10-15 Polls
5. **Phase 2**: Bootstrap nach 20-30 Polls
6. **Phase 3**: Optimierung nach 100+ Polls

---

**Dieses Dokument dient als Diskussionsgrundlage und Spezifikation. Feedback und Anregungen sind willkommen!**

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

**Grundidee**: Jedes Element (hier: Folge) besitzt eine latente **Stärke** π_i (oder im Log-Space: θ_i = log π_i). Die Wahrscheinlichkeit, dass Element i gegenüber Element j bevorzugt wird, folgt der logistischen Funktion: P(i > j) = π_i / (π_i + π_j), was äquivalent zu σ(θ_i - θ_j) ist, wobei σ die logistische Funktion bezeichnet.

**Verbindung zu Logit-Modellen**: Der Log-Odds-Ratio log(P(i > j) / P(j > i)) entspricht der Differenz der Log-Stärken θ_i - θ_j. Dies ist äquivalent zu einem **konditionalen Logit-Modell**, einem Standardwerkzeug in der Discrete Choice Analyse.

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
  - ✅ **Aktuell implementiert** (choix.mm_pairwise unterstützt beide Formate)
  - ❌ Weniger effizient als Binomial-Form (größere Datenmengen)
  - Funktioniert korrekt, mathematisch äquivalent zur Binomial-Form

**Empfehlung**: **Binomial-Counts (w_ij, w_ji) pro Paar** wäre effizienter.

**Aktueller Stand**: Die Implementierung nutzt Disaggregierung (Expansion). Dies funktioniert korrekt, ist aber weniger effizient. Eine Umstellung auf Binomial-Form würde die Performance verbessern, ist aber nicht notwendig für die Korrektheit.

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

**Spaltenname**: `utility` – für normierte Stärken (mean = 1.0).

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

**Ansatz: Append-Only statt Git-basierte Versionierung**

Wir nutzen eine append-only Datei mit Timestamps anstatt die **Git-History** für die Historisierung:

- `ratings.tsv` enthält die Historie aller Bewertungen

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
| **Ausgabeformat** | Normierte Stärken als `utility` | Durchschnitt = 1.0, intuitive Interpretation |
| **Zusatzausgabe** | Win-Prob vs. Durchschnittsfolge: π_i / (π_i + 1) | Prozent-Interpretation |
| **Unsicherheit** | Bootstrap (Phase 2) | choix liefert keine Hesse-Matrix |
| **Konvergenz** | tol = 1e-6, max_iter = 10000 | Standard, ausreichend genau |
| **Zeitdynamik** | Statisch | Folgen ändern sich nicht, Präferenzen driften langsam |
| **Versionierung** | Append-only | ratings.tsv wächst mit jedem Update, ermöglicht Trend-Analysen |
| **Isolierte Folgen** | In Auswertung nur zusammenhängende anzeigen | Keine expliziten Checks, sondern Filter in Visualisierung |

**Anpassungen nach ersten Daten:**
- α über Cross-Validation optimieren
- Bootstrap für Unsicherheitsmaße implementieren

---

## Spezifikation für Implementierung

Dieser Abschnitt definiert konkrete Anforderungen für die Implementierung (Child Issue).

### 1. Input-Spezifikation

**Quelle**: `data/polls.tsv`

**Format**: TSV mit Spalten poll_id, reddit_post_id, created_at, closes_at, episode_a_id, episode_b_id, votes_a, votes_b, finalized_at (siehe data_schema.md für Details)

**Verarbeitung**:
- Nur finalized Polls (finalized_at ist gesetzt)
- Validierung: votes_a, votes_b ≥ 0
- Validierung: episode_a_id ≠ episode_b_id
- Validierung: episode_a_id, episode_b_id existieren in episodes (aus API)

### 2. Likelihood-Formulierung

Die Likelihood basiert auf der Bradley-Terry-Wahrscheinlichkeit P(i > j) = exp(θ_i) / (exp(θ_i) + exp(θ_j)). Die Log-Likelihood summiert über alle Paarvergleiche mit L2-Regularisierung: Summe von w_ij · log P(i > j) + w_ji · log P(j > i) minus dem Regularisierungsterm (α/2) · Summe θ_i².

**Interner Constraint**: Summe θ_i = 0 (wird von choix automatisch enforced)

### 3. Algorithmus

**Verwendung**: choix.mm_pairwise mit MM-Algorithmus

**Parameter**:
- alpha = 0.01 (L2-Regularisierung)
- max_iter = 10000
- tol = 1e-6

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

**Datei**: `data/ratings.tsv` (append-only)

**Spalten**:
- `episode_id`: Folgen-ID (Integer)
- `utility`: Normierte Stärke π_norm,i (Float, mean ≈ 1.0)
- `matches`: Anzahl Vergleiche dieser Folge (Integer)
- `calculated_at`: Zeitstempel der Berechnung (ISO-8601 UTC)

**Formatierung**:
- Floats: 6 Dezimalstellen
- Sortierung: nach episode_id aufsteigend
- Encoding: UTF-8
- Zeilenenden: LF (Unix-Style)

**Versionierung**:
- Datei ist append-only: Neue Berechnungen werden angehängt
- `calculated_at` Timestamp identifiziert jeden Berechnungslauf
- Historie ist direkt in der Datei verfügbar
- Aktuellstes Rating = neuester Timestamp pro Episode

### 6. Fehlerhandling

**Randfälle**:

| Fall | Behandlung |
|------|------------|
| **Poll mit 0 Stimmen** | Warnung loggen, Poll ignorieren |
| **Episode in polls, aber nicht in API** | Fehler werfen, Abbruch |
| **Vergleichsgraph nicht zusammenhängend** | Warnung loggen, nur größte Komponente ranken, Rest in "unranked" |
| **Episode ohne Vergleiche** | Nicht in ratings.tsv enthalten |
| **Numerische Konvergenzprobleme** | Fehler loggen mit Details, Abbruch (nicht still ignorieren) |
| **Keine finalisierten Polls** | Warnung loggen, keine neuen Einträge in ratings.tsv |

### 7. Validierung & Tests

**Vor Deployment**:
- Unit-Tests mit synthetischen Daten (bekannte wahre Stärken)
- Test: Korrelation zwischen geschätzten und wahren Stärken > 0.95
- Test: Konnektivitäts-Check funktioniert
- Test: Fehlerhandling für alle Randfälle
- Test: Normierung korrekt (mean(utility) ≈ 1.0)

**Im CI**:
- Konnektivitäts-Check vor jeder Berechnung
- Warnung, falls neue Folge nicht verbunden
- Plausibilitäts-Checks: mean(utility) ≈ 1.0, std(utility) > 0

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
  - Ausgabeformat: Normierte Stärken als `utility` (mean = 1.0)
  - Datenformat: Disaggregierung (Expansion zu Einzelbeobachtungen)
  - Bibliothek: choix 0.3.5
  - Algorithmus: MM

---

## Offene Fragen und Entscheidungen

### Methodische Fragen

1. **Regularisierung α**:
   - Start mit α = 0.01
   - Wie wird optimales α gewählt? Cross-Validation, Grid-Search oder Empirical Bayes?

2. **Bootstrap für Unsicherheitsmaße**:
   - Anzahl Resamples: 1000? 5000?
   - Resampling-Einheit: Polls (empfohlen) oder Stimmen?
   - Konfidenzintervall: 95%? Perzentil-Methode?

3. **Ankerfolge für Langzeit-Stabilität**:
   - Bei `mean(π) = 1` verschieben sich alle Werte, wenn neue Folgen hinzukommen
   - Alternative: Eine Referenzfolge auf π = 1.0 fixieren
   - Ist Drift langfristig problematisch?

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

## Zusammenfassung

### Was festgelegt ist

✅ **Modell**: Bradley-Terry (logistische Paarwahl)  
✅ **Bibliothek**: choix (Python)  
✅ **Algorithmus**: MM (Minorization-Maximization)  
✅ **Datenformat**: Binomial-Counts (w_ij, w_ji)  
✅ **Regularisierung**: L2 mit α = 0.01 (initial)  
✅ **Interner Constraint**: ∑ θ = 0 (geometric_mean(π) = 1)  
✅ **Ausgabe-Normierung**: mean(π) = 1 (arithmetisches Mittel)  
✅ **Ausgabeformat**: Normierte Stärken als `utility`  
✅ **Versionierung**: Append-only (ratings.tsv wächst mit Updates)  
✅ **Workflow**: polls.tsv → Fit → ratings.tsv (append)  
✅ **Datenformat-Implementierung**: Disaggregierung (Expansion zu Einzelbeobachtungen)

### Was noch zu diskutieren ist

❓ Finale Bestätigung der Default-Parametrisierung  
❓ Details der Bootstrap-Implementierung  
❓ Visualisierung und Community-Präsentation  

---

**Dieses Dokument dient als Diskussionsgrundlage und Methodikspezifikation. Feedback und Anregungen sind willkommen!**

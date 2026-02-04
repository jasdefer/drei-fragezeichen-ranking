# Bradley-Terry-Modell: Recherche und Parametrisierung

Dieses Dokument fasst die Recherche zu Bradley-Terry-Modellen und Discrete Choice Methoden für die Auswertung paarweiser Vergleiche zusammen. Es dient als Diskussionsgrundlage für die Festlegung der Modellparametrisierung.

---

## Inhaltsverzeichnis

1. [Problemstellung](#problemstellung)
2. [Theoretische Grundlagen](#theoretische-grundlagen)
3. [Stand der Praxis in Verhaltensumfragen](#stand-der-praxis-in-verhaltensumfragen)
4. [Verfügbare Ansätze und Bibliotheken](#verfügbare-ansätze-und-bibliotheken)
5. [Zu diskutierende Parametrisierungen](#zu-diskutierende-parametrisierungen)
6. [Offene Fragen und Entscheidungen](#offene-fragen-und-entscheidungen)
7. [Literatur und Referenzen](#literatur-und-referenzen)

---

## Problemstellung

Wir sammeln paarweise Vergleichsdaten über Reddit-Polls („Folge A vs. Folge B"). Aus diesen aggregierten Abstimmungsergebnissen möchten wir ein Ranking aller Folgen ableiten.

**Anforderungen:**
- Umgang mit aggregierten Stimmdaten (z.B. 65 vs. 35 Stimmen)
- Umgang mit unvollständigen Vergleichen (nicht jede Folge wird mit jeder verglichen)
- Stabile Schätzungen auch bei wenigen Vergleichen pro Folge
- Nachvollziehbare, interpretierbare Ergebnisse
- Transparente Methodik

---

## Theoretische Grundlagen

### Das Bradley-Terry-Modell

**Ursprung**: Bradley & Terry (1952) – „Rank Analysis of Incomplete Block Designs"

**Grundidee**: Jedes Element (hier: Folge) besitzt eine latente **Stärke** π_i. Die Wahrscheinlichkeit, dass Element i gegenüber Element j bevorzugt wird, ist:

```
P(i > j) = π_i / (π_i + π_j)
```

**Verbindung zu Logit-Modellen**:
```
log(P(i > j) / P(j > i)) = log(π_i / π_j)
```

Dies ist äquivalent zu einem **konditionalen Logit-Modell**, einem Standardwerkzeug in der Discrete Choice Analyse.

### Einordnung in Discrete Choice

Das Bradley-Terry-Modell ist ein Spezialfall von:
- **Luce's Choice Axiom** (1959): Rational Choice aus endlichen Alternativen
- **Konditionalen Logit-Modellen** (McFadden, 1974): Diskrete Wahlentscheidungen
- **Item Response Theory** (IRT): In der Psychometrie für Paarvergleiche

**Wichtige Eigenschaften:**
- Basiert auf der Annahme der **Independence of Irrelevant Alternatives (IIA)**
- Erlaubt **intransitive Präferenzen** (A > B > C > A möglich)
- Nur **relative Stärken** sind identifizierbar, nicht absolute Werte

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
  - L2-Regularisierung (Ridge): Bestraft extreme Parameterwerte
  - Bayesianische Ansätze: Prior-Verteilungen auf den Stärken
  - Typische Werte: Schwache Regularisierung (α = 0.001 - 0.1)

**Umgang mit aggregierten Daten:**
- **Disaggregierung**: Jede Stimme wird als ein einzelner Vergleich behandelt
  - Vorteil: Einfach, nutzt alle Informationen
  - Nachteil: Kann bei vielen Stimmen ineffizient werden
- **Gewichtete Vergleiche**: Ein Vergleich mit Gewicht = Anzahl Stimmen
  - Vorteil: Effizienter
  - Nachteil: Benötigt erweiterte Implementierungen

**Startwerte:**
- Meist: Gleichverteilte Startwerte (alle Stärken = 1.0 bzw. log-Stärken = 0)
- Alternative: Initiale Schätzungen aus einfacheren Methoden (z.B. Win-Rate)

**Konvergenzkriterien:**
- Toleranz für Parameteränderungen: typisch 1e-6 bis 1e-8
- Maximale Iterationen: 1000-10000
- In der Praxis: Konvergenz nach 100-500 Iterationen bei gut-konditionierten Problemen

---

## Verfügbare Ansätze und Bibliotheken

### 1. choix (Python)

**Repository**: https://github.com/lucasmaystre/choix  
**Entwickler**: Lucas Maystre (EPFL)  
**Status**: Aktiv gewartet, wissenschaftlich fundiert

**Funktionen:**
- ILSR (Iterative Luce Spectral Ranking): Schneller, robuster Algorithmus
- MM (Minorization-Maximization): Garantierte Konvergenz
- Rank Centrality: Spektraler Ansatz ohne Iterationen
- Unterstützt L2-Regularisierung
- Verschiedene Datenformate: Paarvergleiche, Rankings, Top-k

**Verwendung in der Forschung:**
- Publikationen in NIPS, ICML, JMLR
- Verwendet in akademischen Studien zu Crowd-Sourced Rankings

**Vorteile für unser Projekt:**
- Spezialisiert auf Paarvergleiche
- Gut dokumentiert
- Einfache API
- Wissenschaftlich validiert

**Nachteile:**
- Keine dynamischen/zeitabhängigen Modelle
- Keine hierarchischen Modelle (individuelle Unterschiede)

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
**Status**: Standard in der R-Community, sehr ausgereift

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
- Volle Bayesianische Inferenz
- Sehr flexibel, aber komplexer
- Rechenintensiv (MCMC)
- Overkill für unseren Use-Case?

**Scikit-learn (Logistic Regression):**
- Kann für paarweise Vergleiche umformuliert werden
- Nicht spezialisiert, aber vertraut

---

## Zu diskutierende Parametrisierungen

### 1. Regularisierung

**Option A: Keine Regularisierung (Pure MLE)**
- ✅ Theoretisch optimal bei ausreichend Daten
- ❌ Instabil bei wenigen Vergleichen
- ❌ Neue Folgen mit 1-2 Vergleichen problematisch

**Option B: L2-Regularisierung (Ridge)**
- ✅ Stabilisiert Schätzungen
- ✅ Verhindert extreme Werte
- ❌ Bias towards 0 (Mitte)
- ❓ **Wie stark? α = 0.001, 0.01, 0.1?**

**Option C: Bayesianischer Prior**
- ✅ Theoretisch fundiert
- ✅ Flexibel
- ❌ Komplexer, rechenintensiv
- ❌ Schwerer zu erklären

**Frage zur Diskussion:**
- Welche Regularisierung ist für unseren Use-Case sinnvoll?
- Wie stark sollte sie sein?
- Sollen wir adaptive Strategien erwägen (stärkere Regularisierung für Folgen mit wenigen Vergleichen)?

### 2. Datenformat: Aggregiert vs. Disaggregiert

**Option A: Disaggregierung**
- 65 Stimmen für A → 65 Einträge (A beats B)
- ✅ Einfach zu implementieren
- ✅ Nutzt alle Informationen
- ❌ Große Datenmengen bei vielen Stimmen

**Option B: Gewichtete Vergleiche**
- Ein Vergleich mit Gewicht = Anzahl Stimmen
- ✅ Effizienter
- ❌ Nicht alle Bibliotheken unterstützen das
- ❌ Komplexere Implementierung

**Frage zur Diskussion:**
- Wie viele Vergleiche erwarten wir langfristig? (10, 100, 1000?)
- Ist Effizienz ein kritisches Problem?
- Präferenz für einfachere Implementierung?

### 3. Umgang mit unvollständigen Daten

**Problem**: Nicht jede Folge wird mit jeder anderen verglichen.

**Lösung in der Literatur:**
- Bradley-Terry funktioniert gut mit unvollständigen Daten
- **Bedingung**: Vergleichsgraph muss stark zusammenhängend sein
- D.h.: Jede Folge muss über eine Kette von Vergleichen mit jeder anderen verbunden sein

**Frage zur Diskussion:**
- Wie stellen wir sicher, dass neue Folgen schnell genug Vergleiche bekommen?
- Sollen wir aktive Auswahl der Vergleiche nutzen? (z.B. Folgen mit ähnlichen geschätzten Stärken paaren)

### 4. Ausgabeformat

**Option A: Log-Stärken (log π_i)**
- Natürliche Parameterdarstellung
- ❌ Schwer zu interpretieren (negative Werte, keine klare Skala)

**Option B: Rohe Stärken (π_i)**
- ✅ Positive Werte
- ❌ Absolute Skala willkürlich

**Option C: Normierte Stärken (π_i / mean(π))**
- ✅ Durchschnitt = 1.0
- ✅ Werte > 1: überdurchschnittlich, < 1: unterdurchschnittlich
- ✅ Gut interpretierbar

**Option D: Win-Probabilities gegen Durchschnittsfolge**
- P(i beats avg) = π_i / (π_i + π_avg)
- ✅ Intuitive Interpretation (Prozent)
- ❌ Verliert Information bei extremen Werten

**Frage zur Diskussion:**
- Welches Format ist am verständlichsten für die Community?
- Sollen wir mehrere Formate anbieten?

### 5. Zeitliche Dynamik

**Problem**: Präferenzen können sich über die Zeit ändern.

**Option A: Statisches Modell**
- Alle Daten werden gleich gewichtet
- ✅ Einfach
- ❌ Frühe Votes haben gleiche Gewichtung wie späte

**Option B: Zeitabhängiges Modell**
- Ältere Votes werden weniger gewichtet (z.B. exponentielles Decay)
- ✅ Reflektiert Änderungen in Präferenzen
- ❌ Komplexer
- ❓ Wie stark Decay? (Halbwertszeit: 1 Jahr, 6 Monate?)

**Option C: Elo-ähnliches Update-System**
- Stärken werden nach jedem Poll aktualisiert
- ✅ Sehr dynamisch
- ❌ Schwerer nachvollziehbar
- ❌ Keine historische Konsistenz

**Frage zur Diskussion:**
- Erwarten wir signifikante Änderungen in Präferenzen über Zeit?
- Ist ein statisches Modell ausreichend für die ersten 1-2 Jahre?
- Können wir das später erweitern?

### 6. Umgang mit Tie-Gleichständen

**Problem**: Was, wenn ein Poll 50:50 ausgeht?

**Option A: Beide Richtungen**
- 50 Stimmen A → 50x (A beats B)
- 50 Stimmen B → 50x (B beats A)
- ✅ Nutzt alle Informationen
- ✅ Einfach

**Option B: Tie-erweiterte Modelle**
- Explizite Modellierung von Unentschieden
- ✅ Theoretisch sauberer
- ❌ Komplexer
- ❓ Brauchen wir das wirklich?

---

## Offene Fragen und Entscheidungen

### Methodische Fragen

1. **Regularisierung**: Wie stark soll die L2-Regularisierung sein?
   - Vorschlag: Start mit α = 0.01, Sensitivitätsanalyse mit ersten realen Daten

2. **Datenformat**: Disaggregierung oder gewichtete Vergleiche?
   - Vorschlag: Start mit Disaggregierung (einfacher), später bei Bedarf optimieren

3. **Ausgabeformat**: Welche Darstellung der Stärken?
   - Vorschlag: Normierte Stärken (Durchschnitt = 1.0) für die Hauptdarstellung

4. **Zeitliche Dynamik**: Statisch oder dynamisch?
   - Vorschlag: Zunächst statisch, später erweitern falls nötig

### Technische Fragen

5. **Bibliothek**: choix, scipy, oder R?
   - Vorschlag: choix (spezialisiert, gut dokumentiert, Python)
   - Alternative: scipy falls mehr Flexibilität gewünscht

6. **Validierung**: Wie testen wir die Implementierung?
   - Vorschlag: Simulierte Daten mit bekannten Stärken
   - Cross-Validation mit Hold-Out Polls

7. **Transparenz**: Wie dokumentieren wir die Berechnungen?
   - Alle Parameter im Repository dokumentiert
   - Code Open Source und nachvollziehbar
   - Changelog bei Parameteränderungen

### Praktische Fragen

8. **Fehlerhandling**: Was bei zu wenigen Vergleichen?
   - Minimum-Threshold für Aufnahme ins Ranking?
   - Unsicherheitsmaße ausgeben?

9. **Visualisierung**: Wie präsentieren wir die Ergebnisse?
   - Einfache Rangliste
   - Mit Unsicherheitsintervallen?
   - Historische Entwicklung?

10. **Reproduzierbarkeit**: Wie sichern wir ab, dass Berechnungen reproduzierbar sind?
    - Fixierte Bibliotheksversionen
    - Dokumentierte Parameter
    - Versionierte Datensätze

---

## Literatur und Referenzen

### Grundlagenwerke

**Bradley-Terry-Modell:**
1. Bradley, R. A., & Terry, M. E. (1952). *Rank Analysis of Incomplete Block Designs: I. The Method of Paired Comparisons*. Biometrika, 39(3/4), 324-345.

2. Hunter, D. R. (2004). *MM algorithms for generalized Bradley-Terry models*. The Annals of Statistics, 32(1), 384-406.

**Discrete Choice:**
3. Luce, R. D. (1959). *Individual Choice Behavior: A Theoretical Analysis*. Wiley.

4. McFadden, D. (1974). *Conditional logit analysis of qualitative choice behavior*. In P. Zarembka (Ed.), Frontiers in Econometrics (pp. 105-142).

5. Train, K. E. (2009). *Discrete Choice Methods with Simulation* (2nd ed.). Cambridge University Press.

### Praktische Anwendungen

6. Glickman, M. E. (1999). *Parameter estimation in large dynamic paired comparison experiments*. Journal of the Royal Statistical Society: Series C, 48(3), 377-394.
   - Zeitabhängige Bradley-Terry-Modelle

7. Cattelan, M. (2012). *Models for paired comparison data: A review with emphasis on dependent data*. Statistical Science, 27(3), 412-433.
   - Umfassende Übersicht über Erweiterungen

8. Maystre, L., & Grossglauser, M. (2015). *Fast and Accurate Inference of Plackett-Luce Models*. NIPS 2015.
   - Grundlage der choix-Bibliothek

### Software und Tools

9. Maystre, L. (2018). *choix: Inference algorithms for models based on Luce's choice axiom*.
   - https://github.com/lucasmaystre/choix

10. Turner, H., & Firth, D. (2012). *Bradley-Terry Models in R: The BradleyTerry2 Package*. Journal of Statistical Software, 48(9).
    - R-Referenzimplementierung

### Verhaltensforschung und Umfragen

11. Louviere, J. J., Hensher, D. A., & Swait, J. D. (2000). *Stated Choice Methods: Analysis and Applications*. Cambridge University Press.
    - Discrete Choice in Survey Design

12. Agresti, A. (2013). *Categorical Data Analysis* (3rd ed.). Wiley.
    - Statistischer Hintergrund

---

## Nächste Schritte

1. **Diskussion der Parametrisierungen** in diesem Dokument
2. **Entscheidung** über:
   - Regularisierungsstrategie
   - Datenformat
   - Ausgabeformat
   - Bibliothek
3. **Dokumentation der finalen Parameter** in der README
4. **Später**: Implementierung basierend auf den getroffenen Entscheidungen

---

**Dieses Dokument ist als Diskussionsgrundlage gedacht. Alle Fragen und Anregungen sind willkommen!**

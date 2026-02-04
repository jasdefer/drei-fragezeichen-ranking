# Bradley-Terry-Modell: Parametrisierung und Implementierung

Dieses Dokument beschreibt die theoretischen Grundlagen, Parameterauswahl und Implementierung des Bradley-Terry-Modells für die Auswertung der paarweisen Vergleiche von „Die drei ???"-Folgen.

---

## Inhaltsverzeichnis

1. [Einführung](#einführung)
2. [Theoretische Grundlagen](#theoretische-grundlagen)
3. [Bibliotheken und Werkzeuge](#bibliotheken-und-werkzeuge)
4. [Modellparameter](#modellparameter)
5. [Implementierungsempfehlung](#implementierungsempfehlung)
6. [Beispielimplementierung](#beispielimplementierung)
7. [Literatur und Referenzen](#literatur-und-referenzen)

---

## Einführung

Das **Bradley-Terry-Modell** (Bradley & Terry, 1952) ist ein statistisches Modell zur Analyse von **paarweisen Vergleichen**. Es gehört zur Familie der **Discrete Choice Modelle** und basiert auf der Annahme, dass jedes Element (hier: jede Folge) eine latente **Stärke** (auch: Utility, Rating-Parameter) besitzt, die die Wahrscheinlichkeit bestimmt, mit der es in einem direkten Vergleich bevorzugt wird.

### Warum Bradley-Terry?

- ✅ **Spezialisiert auf paarweise Vergleiche**: Perfekt für Reddit-Poll-Format
- ✅ **Statistisch fundiert**: Basiert auf Maximum-Likelihood-Schätzung
- ✅ **Interpretierbar**: Die geschätzten Stärken sind direkt vergleichbar
- ✅ **Robust**: Kann mit inkonsistenten Präferenzen umgehen
- ✅ **Erweiterbar**: Unterstützt Regularisierung und kann auf unvollständige Vergleiche angewandt werden

---

## Theoretische Grundlagen

### Das Bradley-Terry-Modell

Gegeben zwei Folgen \(i\) und \(j\) mit Stärken \(\pi_i\) und \(\pi_j\), modelliert Bradley-Terry die Wahrscheinlichkeit, dass Folge \(i\) gegenüber Folge \(j\) bevorzugt wird:

```
P(i > j) = π_i / (π_i + π_j)
```

Dies entspricht einem **Logit-Modell** (logistische Regression), da:

```
log(P(i > j) / P(j > i)) = log(π_i / π_j)
```

### Eigenschaften

- **Skaleninvarianz**: Nur die relativen Stärken sind bedeutsam, nicht ihre absoluten Werte
- **Nicht-transitivität erlaubt**: Das Modell kann mit Zirkelpräferenzen (A > B > C > A) umgehen
- **Basiert auf Logit-Link**: Verbindung zu multinomialen und konditionalen Logit-Modellen

### Schätzung der Parameter

Die Stärken \(\pi_i\) werden typischerweise mittels **Maximum-Likelihood-Schätzung (MLE)** ermittelt:

- **Zielfunktion**: Maximiere die Log-Likelihood der beobachteten Vergleichsergebnisse
- **Optimierung**: Iterative Verfahren wie Newton-Raphson, Minorization-Maximization (MM), oder Gradient Descent
- **Konvergenz**: Garantiert für stark zusammenhängende Vergleichsgraphen (jede Folge ist über Vergleiche mit jeder anderen verbunden)

---

## Bibliotheken und Werkzeuge

Für die Implementierung des Bradley-Terry-Modells in Python gibt es mehrere etablierte Bibliotheken:

### 1. **choix** (Empfohlen für dieses Projekt)

**Repository**: https://github.com/lucasmaystre/choix  
**Dokumentation**: https://choix.lum.li/

**Vorteile**:
- ✅ Speziell für paarweise Vergleiche entwickelt
- ✅ Implementiert mehrere Algorithmen (LSR, Minorization-Maximization, Rank Centrality)
- ✅ Unterstützt verschiedene Datenformate
- ✅ Einfache API
- ✅ Gut dokumentiert
- ✅ Aktiv gewartet

**Installation**:
```bash
pip install choix
```

**Beispiel**:
```python
import choix

# Paarweise Vergleiche: [(Gewinner, Verlierer), ...]
comparisons = [(0, 1), (0, 2), (1, 2), (2, 1)]

# Bradley-Terry-Modell schätzen
params = choix.ilsr_pairwise(n_items=3, data=comparisons)
print(params)  # Geschätzte Stärken (log-scale)
```

### 2. **scipy** (Alternative für benutzerdefinierte Implementierungen)

Wenn mehr Kontrolle gewünscht ist, kann das Modell mit scipy.optimize direkt implementiert werden:

**Vorteile**:
- ✅ Volle Kontrolle über Optimierung
- ✅ Keine zusätzlichen Abhängigkeiten (scipy bereits weit verbreitet)
- ✅ Flexible Anpassung an spezielle Anforderungen

**Nachteile**:
- ⚠️ Erfordert manuelle Implementierung der Log-Likelihood
- ⚠️ Mehr Code zu warten

### 3. **BradleyTerry2** (R-Paket, nicht Python)

Für Referenz: In R gibt es das etablierte Paket `BradleyTerry2`, das als Benchmark für Ergebnisse dienen kann.

---

## Modellparameter

Die Qualität und Stabilität der geschätzten Stärken hängt von mehreren Parametern ab:

### 1. **Regularisierung** (Empfohlen: L2-Regularisierung)

**Problem**: Bei wenigen Vergleichen können die MLE-Schätzungen instabil werden oder divergieren.

**Lösung**: L2-Regularisierung (Ridge-Regression im Logit-Raum)

```
Penalisierte Log-Likelihood: 
ℓ_pen(π) = ℓ(π) - (λ/2) * Σ_i (log π_i)²
```

**Parameter**:
- **`alpha` (λ)**: Regularisierungsstärke
  - **Empfehlung für dieses Projekt**: `alpha = 0.01` (schwache Regularisierung)
  - Begründung: Verhindert Instabilität bei neuen Folgen mit wenigen Vergleichen, während etablierte Folgen kaum beeinflusst werden
  - Anpassung: Bei sehr wenigen Daten (< 10 Vergleiche pro Folge im Durchschnitt) auf `alpha = 0.1` erhöhen

**Beispiel mit choix**:
```python
params = choix.ilsr_pairwise(n_items=3, data=comparisons, alpha=0.01)
```

### 2. **Startwerte** (Initial Values)

**Problem**: Iterative Optimierungsalgorithmen benötigen Startwerte für die Parameter.

**Empfehlung**:
- **Gleichverteilte Startwerte**: `π_i = 1.0` für alle Folgen (bzw. `log π_i = 0`)
- Begründung: Neutrale Startposition, keine Vorannahmen über Präferenzen
- Alternative: Wenn Vorabinformationen existieren (z.B. alte Rankings), können diese als Startwerte dienen

**Hinweis**: Bei choix werden Startwerte automatisch initialisiert (typischerweise mit Null im Log-Space).

### 3. **Konvergenzkriterien**

Die Optimierung stoppt, wenn eine der folgenden Bedingungen erfüllt ist:

**Parameter**:
- **`tol` (Tolerance)**: Maximale Änderung der Parameter zwischen Iterationen
  - **Empfehlung**: `tol = 1e-6`
  - Begründung: Balance zwischen Genauigkeit und Rechenzeit
  
- **`max_iter`**: Maximale Anzahl von Iterationen
  - **Empfehlung**: `max_iter = 10000`
  - Begründung: Verhindert unendliche Schleifen bei Konvergenzproblemen
  - In der Praxis konvergiert das Modell typischerweise in 100-500 Iterationen

**Beispiel mit choix**:
```python
params = choix.ilsr_pairwise(
    n_items=n_items,
    data=comparisons,
    alpha=0.01,
    max_iter=10000
)
```

### 4. **Behandlung von Gewichten** (Optional)

Reddit-Polls liefern **aggregierte Stimmen** (z.B. „Folge A: 65 Stimmen, Folge B: 35 Stimmen").

**Ansatz 1: Disaggregierung** (Empfohlen für kleine Datensätze)
- Jede Stimme wird als einzelner paarweiser Vergleich behandelt
- Beispiel: 65 Stimmen für A → 65 Einträge (A, B) in den Vergleichsdaten
- Vorteil: Einfach, nutzt alle Informationen
- Nachteil: Große Datenmenge bei vielen Stimmen

**Ansatz 2: Gewichtete Vergleiche** (Empfohlen für große Datensätze)
- Ein Vergleich mit Gewicht = Anzahl der Stimmen
- Erfordert erweiterte Implementierung (choix unterstützt dies über `opt_pairwise` mit Gewichten)
- Vorteil: Effizienter bei vielen Stimmen

**Empfehlung für dieses Projekt**:
- **Start**: Disaggregierung (Ansatz 1), da die Anzahl der Vergleiche überschaubar ist
- **Später**: Bei > 100 Polls auf gewichtete Vergleiche umsteigen

### 5. **Skalierung der Ausgabe**

Die geschätzten Stärken sind auf einer **Log-Skala** und relativ zueinander.

**Transformationen für bessere Interpretierbarkeit**:

1. **Exponentielle Transformation**: `π_i = exp(log_π_i)`
   - Ergibt positive Stärken
   - Verhältnisse bleiben erhalten: `π_i / π_j = exp(log_π_i - log_π_j)`

2. **Normierung auf Durchschnitt**: `π_i_norm = π_i / mean(π)`
   - Durchschnitt = 1.0
   - Werte > 1: überdurchschnittlich beliebt
   - Werte < 1: unterdurchschnittlich beliebt

3. **Wahrscheinlichkeits-Interpretation**:
   - Win-Probability gegen durchschnittliche Folge: `P(i > avg) = π_i / (π_i + π_avg)`

---

## Implementierungsempfehlung

### Empfohlener Workflow

1. **Datenaufbereitung**:
   - Lade alle Polls aus `data/polls.tsv`
   - Konvertiere aggregierte Stimmen in paarweise Vergleiche
   - Format: Liste von Tupeln `[(winner_id, loser_id), ...]`

2. **Modellschätzung**:
   - Nutze `choix.ilsr_pairwise()` mit L2-Regularisierung (`alpha=0.01`)
   - Setze `max_iter=10000` zur Sicherheit

3. **Ergebnisaufbereitung**:
   - Transformiere Log-Stärken: `utility = exp(log_strength)`
   - Normiere auf Durchschnitt: `normalized_utility = utility / mean(utility)`
   - Zähle Anzahl der Vergleiche pro Folge

4. **Speicherung**:
   - Schreibe Ergebnisse in `data/ratings.tsv` (append-only mit Timestamp)
   - Spalten: `episode_id`, `utility`, `matches`, `calculated_at`

### Qualitätssicherung

- **Validierung**: Prüfe, dass alle Stärken positiv sind
- **Plausibilität**: Folgen mit mehr Stimmen sollten extremere Werte haben
- **Konvergenz**: Logge die Anzahl der Iterationen und prüfe, dass `max_iter` nicht erreicht wurde

---

## Beispielimplementierung

Siehe `examples/bradley_terry_example.py` für eine vollständige Implementierung mit Dummy-Daten.

### Minimales Beispiel

```python
import choix
import numpy as np
from datetime import datetime
from pathlib import Path

def load_polls(tsv_path):
    """Lädt Polls aus TSV und konvertiert zu paarweisen Vergleichen."""
    comparisons = []
    episode_ids = set()
    
    with open(tsv_path, 'r') as f:
        next(f)  # Skip header
        for line in f:
            parts = line.strip().split('\t')
            ep_a, ep_b = int(parts[4]), int(parts[5])
            votes_a, votes_b = int(parts[6]), int(parts[7])
            
            episode_ids.update([ep_a, ep_b])
            
            # Disaggregierung: jede Stimme als ein Vergleich
            for _ in range(votes_a):
                comparisons.append((ep_a, ep_b))
            for _ in range(votes_b):
                comparisons.append((ep_b, ep_a))
    
    return comparisons, sorted(episode_ids)

def compute_bradley_terry_ratings(comparisons, episode_ids):
    """Berechnet Bradley-Terry-Stärken."""
    n_items = len(episode_ids)
    
    # Mappe episode_ids zu Indizes 0, 1, 2, ...
    id_to_idx = {ep_id: idx for idx, ep_id in enumerate(episode_ids)}
    indexed_comparisons = [
        (id_to_idx[winner], id_to_idx[loser]) 
        for winner, loser in comparisons
    ]
    
    # Bradley-Terry mit L2-Regularisierung
    log_strengths = choix.ilsr_pairwise(
        n_items=n_items,
        data=indexed_comparisons,
        alpha=0.01,
        max_iter=10000
    )
    
    # Transformation: Log → Utility (normiert auf Durchschnitt)
    utilities = np.exp(log_strengths)
    normalized_utilities = utilities / np.mean(utilities)
    
    # Zähle Matches pro Folge
    match_counts = {ep_id: 0 for ep_id in episode_ids}
    for winner, loser in comparisons:
        match_counts[winner] += 1
        match_counts[loser] += 1
    
    return {
        'episode_ids': episode_ids,
        'utilities': normalized_utilities,
        'match_counts': [match_counts[ep_id] for ep_id in episode_ids]
    }

def save_ratings(results, output_path):
    """Speichert Ratings im TSV-Format (append-only)."""
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    with open(output_path, 'a') as f:
        for ep_id, utility, matches in zip(
            results['episode_ids'],
            results['utilities'],
            results['match_counts']
        ):
            f.write(f"{ep_id}\t{utility:.6f}\t{matches}\t{timestamp}\n")

# Hauptworkflow
if __name__ == '__main__':
    polls_path = Path('data/polls.tsv')
    ratings_path = Path('data/ratings.tsv')
    
    comparisons, episode_ids = load_polls(polls_path)
    results = compute_bradley_terry_ratings(comparisons, episode_ids)
    save_ratings(results, ratings_path)
    
    print(f"✓ Ratings für {len(episode_ids)} Folgen berechnet")
    print(f"✓ Basierend auf {len(comparisons)} paarweisen Vergleichen")
```

---

## Literatur und Referenzen

### Wissenschaftliche Grundlagen

1. **Bradley, R. A., & Terry, M. E. (1952)**  
   *Rank Analysis of Incomplete Block Designs: I. The Method of Paired Comparisons*  
   Biometrika, 39(3/4), 324-345.  
   → Originalarbeit zum Bradley-Terry-Modell

2. **Hunter, D. R. (2004)**  
   *MM algorithms for generalized Bradley-Terry models*  
   The Annals of Statistics, 32(1), 384-406.  
   → Effiziente Algorithmen für die Parameterschätzung

3. **Agresti, A. (2013)**  
   *Categorical Data Analysis* (3rd ed.), Wiley  
   → Kapitel zu Paired Comparisons und Log-Linear Models

### Software und Implementierung

4. **choix Library**  
   Maystre, L. (2018). choix: Inference algorithms for models based on Luce's choice axiom.  
   https://github.com/lucasmaystre/choix  
   → Empfohlene Python-Bibliothek

5. **BradleyTerry2 (R)**  
   Turner, H., & Firth, D. (2012). Bradley-Terry Models in R: The BradleyTerry2 Package.  
   Journal of Statistical Software, 48(9).  
   → Referenzimplementierung in R

### Discrete Choice Modelle (Kontext)

6. **Train, K. E. (2009)**  
   *Discrete Choice Methods with Simulation* (2nd ed.), Cambridge University Press  
   → Umfassende Einführung in Discrete Choice-Modelle

7. **McFadden, D. (1974)**  
   *Conditional logit analysis of qualitative choice behavior*  
   In P. Zarembka (Ed.), Frontiers in Econometrics (pp. 105-142)  
   → Theoretische Grundlagen von Logit-Modellen

### Anwendungen und Erweiterungen

8. **Glickman, M. E. (1999)**  
   *Parameter estimation in large dynamic paired comparison experiments*  
   Journal of the Royal Statistical Society: Series C, 48(3), 377-394  
   → Dynamische Bradley-Terry-Modelle (z.B. Elo-Rating)

9. **Cattelan, M. (2012)**  
   *Models for paired comparison data: A review with emphasis on dependent data*  
   Statistical Science, 27(3), 412-433  
   → Übersicht über Erweiterungen des Bradley-Terry-Modells

---

## Zusammenfassung: Empfohlene Parameter

| Parameter | Wert | Begründung |
|-----------|------|------------|
| **Bibliothek** | `choix` | Spezialisiert, gut dokumentiert, aktiv gewartet |
| **Algorithmus** | `ilsr_pairwise` | Effizient, robust, unterstützt Regularisierung |
| **Regularisierung** | `alpha = 0.01` | Schwache L2-Regularisierung für Stabilität |
| **Max. Iterationen** | `max_iter = 10000` | Verhindert Endlosschleifen |
| **Konvergenztoleranz** | `tol = 1e-6` | Ausreichende Genauigkeit (choix-Default) |
| **Startwerte** | Uniform (0 im Log-Space) | Neutral, keine Vorannahmen |
| **Datenformat** | Disaggregiert | Jede Stimme als ein Vergleich (für kleine Datensätze) |
| **Ausgabeformat** | Normiert auf Durchschnitt | `utility / mean(utility)` für Interpretierbarkeit |

Diese Parameter sind für den Projektstart geeignet und können bei Bedarf angepasst werden, wenn mehr Daten vorliegen.

---

**Nächste Schritte**:
1. Installation von `choix`: `pip install choix`
2. Implementierung der Berechnungslogik (siehe Beispiel oben)
3. Integration in GitHub Actions Workflow
4. Testen mit ersten realen Poll-Daten

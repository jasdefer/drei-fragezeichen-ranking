# Matchmaking für Paarvergleiche (Die drei ???) – Spezifikation

Diese Datei beschreibt das Verfahren zur Auswahl neuer Matches (Reddit-Polls) für ein community-getriebenes Ranking der Hörspielfolgen mittels **Bradley–Terry** (BT).  
Ziel ist eine **nachvollziehbare, datenbasierte** Match-Auswahl, die

- einen **zusammenhängenden Vergleichsgraphen** sicherstellt (BT identifizierbar),
- **Unsicherheit effizient reduziert** (statt zufälliger Matches),
- **chronologisch** (poolweise) erweitert werden kann,
- **Wiederholungen** und **Poll-Fatigue** durch Diversität reduziert,
- deterministisch genug für Nachvollziehbarkeit, aber **stochastisch** genug für Vielfalt bleibt.

> Annahme: **keine Drift** (Präferenzen sind zeitlich stationär).  
> Anomalien/Brigading werden zunächst ignoriert.

---

## Begriffe

- **Episode / Alternative**: eine Hörspielfolge.
- **Poll**: ein Reddit-Vergleich zwischen zwei Episoden `(i, j)` mit aggregierten Stimmen.
- **θ_i**: latente BT-Stärke (sum-to-zero constraint).
- **π_i = exp(θ_i)**: positive Stärke auf intuitiver Skala; anschließend auf `mean(π)=1` renormiert (Ausgabe).
- **Vergleichsgraph**: Knoten = Episoden, Kante zwischen i und j wenn mindestens ein Poll existiert.
- **Connected**: Vergleichsgraph hat genau **eine** Zusammenhangskomponente.

---

## Daten / State (für Matchmaking)

Pro Episode `i` werden geführt:

- `n_total[i]` : Anzahl Polls, in denen Episode i vorkam
- `n_calib[i]` : Anzahl **Kalibrierungs-Polls** (Definition unten)
- `last_seen_poll_idx[i]` : Index des letzten Polls mit Episode i (für Recency)
- `activated[i]` : ob Episode i dauerhaft im Pool ist (siehe Active-Set-Regeln)

Zusätzlich:

- `component_id[i]` : Komponentenzuordnung im Vergleichsgraph (Union-Find/DSU)
- `poll_count` : laufender Poll-Index (0, 1, 2, …)
- `pair_history` (optional): z.B. letzter Poll-Index pro Paar `(i,j)` für Repeat-Malus  
  *(nicht zwingend, da wir Wiederholungen primär über geringe Information/Recency indirekt vermeiden; kann aber für Zusatzmalus genutzt werden)*

---

## Parameter (Defaults)

### Pool & Kalibrierung
- `K_seed = 8` : Seed-Pool umfasst Episoden 1..8
- `frontier_size = 4` : gleichzeitig „neue“ Episoden zur Aktivierung
- `d_min = 6` : Mindestanzahl Polls pro Episode für „calibrated“
- `m_min = 2` : Mindestanzahl Kalibrierungs-Polls pro Episode für „calibrated“
- `min_anchor_for_uncal_vs_uncal = 1` : uncalibrated-vs-uncalibrated nur erlaubt, wenn beide mindestens 1 Calibration hatten (empfohlen)

### Recency
- `tau_rec = 4` : Zeitskala in Polls (exponentieller Bonus für „lange nicht dran“)

### Bootstrap (Uncertainty Engine)
- Start nach `Y_boot = 20` Polls
- Update-Frequenz `X_boot = 5` (alle 5 Polls neu berechnen)
- Resamples `B_boot = 200`
- Poll-Resampling-Gewicht `w_k = sqrt(n_votes_k)` (robust)

### Stochastische Auswahl
- `K_candidates = 100` : Auswahl per Softmax aus Top-K Paaren
- Temperatur `T = 0.3`
- Exploration `epsilon = 0.05` (5% random aus eligible)

### Scoring-Gewichte (Startwerte)
Vor Bootstrap (kein q verfügbar):
- `w_close = 0.6`
- `w_unc  = 0.6`
- `w_cal  = 1.0`
- `w_rec  = 0.4`
- `w_q    = 0.0`

Nach Bootstrap:
- `w_close = 0.2` (optional kleiner)
- `w_unc  = 0.6`
- `w_cal  = 1.0`
- `w_rec  = 0.4`
- `w_q    = 1.0`

> Gewichte sind Tuning-Parameter. Wichtig ist die Rangordnung: **Kalibrierung + Uncertainty** dominieren, Recency sorgt für Vielfalt.

---

## Zustände pro Episode

- **unobserved**: `n_total[i] == 0`
- **uncalibrated**: nicht calibrated und bereits mindestens 1 Vergleich
- **calibrated**:
  - `n_total[i] >= d_min` AND `n_calib[i] >= m_min`

### Kalibrierungs-Poll
Ein Poll `(i,j)` ist ein Kalibrierungs-Poll **für i**, wenn:
- i ist **uncalibrated** (oder nicht calibrated) und
- j ist **calibrated** (oder Seed-Anchor, falls später eingeführt)
Dann: `n_calib[i] += 1`.

---

## Active Set / Frontier-Regeln

### Aktivierter Pool
- Initial: `activated = {1..K_seed}`

### Frontier (rollierend)
- Zu jedem Zeitpunkt existiert `frontier` als die nächsten `frontier_size` noch nicht aktivierten Episoden (chronologisch).
- **Sobald eine Frontier-Episode in einem Poll vorkommt**, wird sie `activated = true`.  
  Danach rückt die nächste chronologische Episode nach, sodass wieder `frontier_size` Frontier-Episoden verfügbar sind.

### Active Set
- `active_set = activated ∪ frontier`

Matchmaking darf **nur** Paare aus `active_set` wählen.

---

## Phasen des Verfahrens

### Phase 0: Seed (League-Shift, K=8)

Ziel: schnell ein connected Grundnetz erzeugen, ohne sofortige Dopplungen und ohne künstliche „Episode-1-überall“-Brücken.

Seed-Rounds (Beispiel, K=8):
- Round 1: (1v2), (3v4), (5v6), (7v8)
- Round 2: (2v3), (4v5), (6v7)  *(und optional 8v1, falls gewünscht; kann auch weggelassen werden)*

Minimal genügt meist:
- Round 1 + Round 2, damit der Graph der 8 Folgen sehr schnell connected wird.

> Danach wird **bereits** das normale Auswahlverfahren genutzt, aber zunächst ohne Frontier-Aktivierung (oder Frontier=0), bis der Seed-Pool ausreichend stabil ist.

---

### Phase 1: Normalbetrieb (Adaptive Auswahl)

- Active Set = activated ∪ frontier (Frontier rolliert)
- Eligible-Paare nach Hard-Constraints
- Scoring → Softmax → Poll posten
- Nach Poll-Ende: Daten einlesen → BT-Fit aktualisieren → ggf. Bootstrap aktualisieren

---

## Hard-Constraints (Candidate Filtering)

Für jedes Kandidatenpaar `(i,j)` aus `active_set`, `i<j`:

1) **No unobserved vs unobserved**
- Wenn `n_total[i]==0` AND `n_total[j]==0` → nicht eligible.

2) **Gate für uncalibrated vs uncalibrated** (empfohlen)
- Wenn beide nicht calibrated:
  - erlaube nur, wenn beide mindestens `min_anchor_for_uncal_vs_uncal` Calibration-Matches haben.

3) **Connectivity-Phase Constraint** (nur wenn aktiv)
- erlaube nur `(i,j)`, wenn `component_id[i] != component_id[j]`.

> Keine harte Pair-Dedup-Regel: Wiederholungen werden über Score/Softmax unattraktiv, nicht verboten.

---

## Scoring (alles auf 0..1 normiert)

Für jedes eligible Paar `(i,j)`:

### 1) Closeness aus Modell-p
\[
p_{ij}=\sigma(\theta_i-\theta_j)
\]
\[
S_{close}(i,j)=1-2\cdot|p_{ij}-0.5|
\]
Range 0..1 (max bei 0.5)

### 2) Order-uncertainty aus Bootstrap-q (wenn verfügbar)
\[
q_{ij}=P(\theta_i>\theta_j)\ \text{über Bootstrap}
\]
\[
S_q(i,j)=1-2\cdot|q_{ij}-0.5|
\]
Range 0..1

Wenn Bootstrap noch nicht aktiv: `S_q = 0`.

### 3) Uncertainty / Under-sampling
Fallback (vor Bootstrap):
\[
U(i)=\frac{1}{\sqrt{n_{total}[i]+1}}
\]
Normierung: skaliere U(i) über active_set auf 0..1 (min/max).

Dann:
\[
S_{unc}(i,j)=\frac{U(i)+U(j)}{2}
\]

Nach Bootstrap:
- nutze `sd_theta[i]` oder CI-Breite statt U(i) (ebenfalls auf 0..1 normieren)
- `S_unc(i,j) = mean(sd_norm(i), sd_norm(j))`

### 4) Calibration-Bonus
\[
S_{cal}(i,j)=
\begin{cases}
1 & \text{wenn genau eine Episode uncalibrated und die andere calibrated ist}\\
0 & \text{sonst}
\end{cases}
\]

### 5) Recency-Bonus (episodenbasiert, exponentiell)
Für Episode i:
- `age_i = poll_count - last_seen_poll_idx[i]` (wenn nie gesehen: setze age groß)
\[
R(i)=1-\exp(-age_i/\tau_{rec})
\]
Dann:
\[
S_{rec}(i,j)=\frac{R(i)+R(j)}{2}
\]

### Gesamtscore (linear)
Vor Bootstrap:
\[
Score = w_{close}S_{close} + w_{unc}S_{unc} + w_{cal}S_{cal} + w_{rec}S_{rec}
\]

Nach Bootstrap:
\[
Score = w_{q}S_{q} + w_{close}S_{close} + w_{unc}S_{unc} + w_{cal}S_{cal} + w_{rec}S_{rec}
\]

---

## Stochastische Auswahl (Softmax + Exploration)

1) Berechne `Score(i,j)` für alle eligible Paare.
2) Sortiere absteigend, nimm Top `K_candidates`.
3) Softmax-Gewichte:
\[
w_{ij}=\exp(Score(i,j)/T)
\]
\[
P_{ij}=w_{ij}/\sum w
\]
4) Ziehe ein Paar `(i,j)` gemäß `P`.

Optional ε-greedy:
- mit Wahrscheinlichkeit `epsilon`: ziehe uniform zufällig aus allen eligible Paaren.

---

## Bootstrap-Spezifikation (Weighted Poll Bootstrap)

Bootstrap läuft erst ab `poll_count >= Y_boot`, danach alle `X_boot` Polls.

### Input
Liste aller abgeschlossenen Polls:
- `(i_k, j_k, votes_i_k, votes_j_k, n_k=votes_i_k+votes_j_k)`

### Resampling
Für jedes Bootstrap b=1..B:
- Ziehe M Polls **mit Replacement** aus der Poll-Liste
- Zieh-Wahrscheinlichkeit proportional zu `sqrt(n_k)` (oder `n_k`, falls gewünscht)
- Fitte BT auf dem resample → erhalte `θ^(b)`

### Outputs
- `sd_theta[i] = std_b(θ_i^(b))`
- Optional on-demand:
  - `q_ij = mean_b(θ_i^(b) > θ_j^(b))` für Kandidatenpaare

---

## Caching / Speicherung von Bootstrap-Ergebnissen

Da maximal ~250 Episoden erwartet werden, sind vollständige Paarmatrizen handhabbar:

- 250×250 = 62.500 Einträge (symmetrisch, diagonal trivial)

Empfohlen:

1) `bootstrap_theta_sd.tsv`
- Spalten: `episode_id`, `sd_theta`, `updated_at_poll_idx`

2) `bootstrap_q_matrix.tsv` (optional, aber möglich)
- Formatvorschläge:
  - Wide: Header = episode_ids, Zeilen = episode_ids (Matrix)
  - Long (sparsam/üblich): `i`, `j`, `q_ij`, `updated_at

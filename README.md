# Drei ??? – Community Ranking via Pairwise Polls

Dieses Projekt erstellt ein community-getriebenes Ranking der **Hörspielfolgen von „Die drei ???“** auf Basis regelmäßiger Reddit-Umfragen.

Statt klassischer Einzelbewertungen (z. B. 1–100-Skalen) setzen wir auf **paarweise Vergleiche** („Folge A vs. Folge B“) und werten diese mit einem statistischen Modell aus dem Bereich **Discrete Choice** aus.

Das Ziel ist kein „endgültiges Urteil“, sondern ein **transparentes, datenbasiertes Ranking**, das mit jeder Umfrage besser wird – und bei dem die Datenerhebung selbst Spaß macht.

---

## Motivation & Abgrenzung zu bestehenden Bewertungen

Viele bestehende Rankings bewerten jede Folge **isoliert**:
- Sterne, Punkte, Schulnoten
- starke subjektive Verzerrung
- schwer vergleichbar über Zeit und Nutzer hinweg

Dieses Projekt geht bewusst einen anderen Weg:

- Nutzer treffen **konkrete Entscheidungen** („Welche höre ich lieber?“)
- Entscheidungen sind **relativ**, nicht absolut
- Die Auswertung folgt Methoden aus der **wissenschaftlichen Präferenzforschung (Discrete Choice)**

Paarweise Vergleiche sind präziser, weil:
- Menschen besser vergleichen als skalieren
- Ergebnisse konsistenter sind
- extreme oder inkonsistente Einzelurteile weniger Einfluss haben

Der Nachteil:  
Es werden **mehr Daten** benötigt.  
Der Vorteil:  
Diese Datenerhebung passiert spielerisch – über regelmäßige Matches.

---

## Methodik: Discrete Choice & Bradley–Terry

Jede Folge besitzt eine **latente Stärke** („wie sehr wird sie bevorzugt?“).

Bei einer Umfrage zwischen zwei Folgen:
- Stimmen werden als **Präferenzdaten** interpretiert
- klare Siege (z. B. 80 / 20) liefern mehr Information als knappe
- das Modell passt die Stärken so an, dass die beobachteten Entscheidungen möglichst gut erklärt werden

Konkret verwenden wir ein **Bradley–Terry-Modell**, ein logistisches Discrete-Choice-Modell für paarweise Vergleiche.

Wichtig:
- Das Ranking ist **ein Modell**, keine Wahrheit
- Präferenzen müssen **nicht transitiv** sein
- Das Ergebnis ist immer eine **Annäherung**, die mit mehr Daten stabiler wird

### Modellparameter und Implementierung

Das Projekt verwendet folgende Parameter für das Bradley-Terry-Modell:

- **Bibliothek**: [`choix`](https://choix.lum.li/) – Python-Bibliothek für Discrete Choice
- **Algorithmus**: ILSR (Iterative Luce Spectral Ranking) mit Maximum-Likelihood-Schätzung
- **Regularisierung**: L2-Regularisierung mit `alpha = 0.01` (schwache Regularisierung für Stabilität)
- **Konvergenz**: `max_iter = 10000`, `tol = 1e-6`
- **Ausgabeformat**: Normierte Utilities (Durchschnitt = 1.0)

**Detaillierte Dokumentation**: [docs/bradley_terry_model.md](docs/bradley_terry_model.md)  
**Beispielimplementierung**: [examples/bradley_terry_example.py](examples/bradley_terry_example.py)

---

## Projektziele

- Spaß an direkten Folge-Duellen
- Ein transparentes, nachvollziehbares Ranking
- Keine Blackbox-Bewertungen
- Offener, experimenteller Ansatz
- Vollständig Open Source

---

## Architekturüberblick

Das Projekt kommt **ohne Server und ohne Datenbank** aus.

**Komponenten:**
- **GitHub Actions**  
  Automatisierte Ausführung (Posten, Auswerten, Aktualisieren)
- **Reddit**  
  Native Polls als Datenerhebung
- **CSV-Dateien im Repository**  
  Persistente, versionierte Datenspeicherung
- **GitHub Pages**  
  Öffentliche Darstellung der Ergebnisse

**Warum dieser Ansatz?**
- wenige „moving parts“
- hohe Transparenz
- reproduzierbar
- keine laufenden Kosten
- kein eigener Betrieb notwendig

---

## Datenhaltung (konzeptionell)

Es werden drei Arten von Daten gehalten:

1. **Episoden-Stammdaten**
   - Folgennummer
   - Titel
   - Erscheinungsjahr
   - Typ (regulär / Sonderfolge)
   - optionale Kurzbeschreibung

2. **Umfragen (Polls)**
   - welche zwei Folgen verglichen wurden
   - Start- und Endzeit
   - aggregierte Stimmen pro Option

3. **Bewertungen / Stärken**
   - geschätzte Stärke pro Folge
   - Anzahl ausgewerteter Vergleiche

Prinzipien:
- keine Redundanz
- alles ableitbar
- vollständige Historie über Git

---

## Ablauf eines Umfrage-Zyklus

1. Zwei Folgen werden ausgewählt
2. Ein nativer Reddit-Poll wird erstellt (Laufzeit: 7 Tage)
3. Der Poll schließt automatisch
4. Stimmen werden ausgelesen
5. Das Modell wird **einmalig** aktualisiert
6. Das öffentliche Ranking wird neu generiert

Es gibt **keine Zwischen-Updates** während einer laufenden Umfrage.

---

## Veröffentlichung der Ergebnisse

Die aktuellen Ergebnisse sind öffentlich über **GitHub Pages** einsehbar:
- Rangliste aller Folgen
- methodische Erklärung
- Download der Rohdaten (CSV)

Es werden **keine personenbezogenen Daten** gespeichert:
- keine Reddit-Usernamen
- keine Einzelstimmen
- nur aggregierte Poll-Ergebnisse

---

## Governance & Spielregeln

- Feste Posting-Kadenz (derzeit: max. zwei parallele Umfragen)
- Keine manuelle Manipulation von Ergebnissen
- Methodische Änderungen werden dokumentiert
- Das Projekt ist experimentell und iterativ
- Beiträge, Feedback und Kritik sind willkommen

---

## Roadmap

- Start mit kleiner Teilmenge von Folgen
- schrittweise Erweiterung des Episoden-Pools
- Weiterentwicklung der Match-Auswahl (Informationsgewinn)
- Verbesserte Visualisierung der Ergebnisse

---

## Open Source

Dieses Projekt ist vollständig Open Source.

Ziel ist nicht nur ein Ranking, sondern ein **nachvollziehbarer Prozess**, der zeigt, wie Community-Präferenzen strukturiert erhoben und ausgewertet werden können.

Pull Requests, Ideen und Diskussionen sind ausdrücklich erwünscht.

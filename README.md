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

### Recherche und Parametrisierung

Die Parametrisierung des Modells ist festgelegt und dokumentiert.

**Methodikdokument**: [docs/bradley_terry_research.md](docs/bradley_terry_research.md)

Dieses Dokument beschreibt:
- Theoretische Grundlagen und Discrete Choice Methoden
- Stand der Praxis in Verhaltensumfragen
- Verwendete Bibliothek (choix) und Algorithmus (MM)
- Festgelegte Parametrisierung (Regularisierung α = 0.01, Datenformat, Ausgabeformat)
- bekannte Einschränkungen und Implementierungsdetails

**Datenmodell**: [docs/data_schema.md](docs/data_schema.md) beschreibt die Datenstrukturen (polls.tsv, ratings.tsv, API-Zugriff)

---

## Projektziele

- Spaß an direkten Folge-Duellen
- Ein transparentes, nachvollziehbares Ranking
- Keine Blackbox-Bewertungen
- Offener, experimenteller Ansatz
- Vollständig Open Source

---

## Architekturüberblick

Das Projekt kommt **ohne Server und ohne Datenbank** aus und setzt auf kleine Python-Helfer, die in Workflows eingebunden werden können.

### Bereits umgesetzt

- **Dreimetadaten-API-Wrapper** für Episoden-Stammdaten
- **TSV-Repository-Schicht** für `polls.tsv` und `ratings.tsv`
- **Bradley-Terry-Auswertung** als Python-Modul (append-only nach `ratings.tsv`)
- **Datenvalidierung** als leichtgewichtiger Helper-Aufruf
- **Automatisierte Tests** für Modelllogik und API-Wrapper

### Geplant

- **Reddit-Integration** (Polls posten und Ergebnisse einlesen)
- **GitHub Actions** für zeitgesteuerte und automatisierte Abläufe
- **GitHub Pages** für öffentliche Darstellung des aktuellen Rankings
- **Matchmaking-Automatisierung** für die Paar-Auswahl

**Warum dieser Ansatz?**
- wenige „moving parts“
- hohe Transparenz
- reproduzierbar
- keine laufenden Kosten
- modular erweiterbar

---

## Datenhaltung (konzeptionell)

Es werden drei Arten von Daten gehalten:

1. **Episoden-Stammdaten (API-basiert)**
   - Folgennummer (`nummer`) als Primärreferenz
   - bei Bedarf Metadaten wie Titel/Beschreibung/Cover-URL

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

## Ablauf im aktuellen Stand

Aktuell ist vor allem der **Auswertungs- und Datenpflege-Teil** umgesetzt:

1. Poll-Daten liegen in `data/prod/polls.tsv` vor
2. Die Daten werden validiert (Schema, API-Referenzen und Formatprüfungen)
3. Das Bradley-Terry-Modell berechnet daraus Utilities
4. Neue Snapshot-Zeilen werden append-only nach `data/prod/ratings.tsv` geschrieben

Das Posting/Einlesen von Reddit-Polls ist als nächster Schritt geplant.

---

## Veröffentlichung der Ergebnisse

Die öffentliche Aufbereitung erfolgt über **GitHub Pages** mit einem statischen Build aus `data/prod/ratings.tsv`.

Der Build wird lokal oder in CI über folgenden Befehl erzeugt:

```bash
python -m bot build-site --output-dir site --ratings-file data/prod/ratings.tsv --polls-file data/prod/polls.tsv
```

Für lokale Entwicklung gibt es getrennte Datenumgebungen:
- `data/prod/` für Produktionsdaten
- `data/test/` für synthetische Testdaten und UI-Entwicklung

Beispiel Test-Build:

```bash
python -m bot build-site --output-dir site-test --ratings-file data/test/ratings.tsv --polls-file data/test/polls.tsv
```

PowerShell + Docker (ohne lokales Python) fuer schnellen Testlauf:

```powershell
# 1) Test-Site bauen (inkl. Polls -> Ratings Update)
docker run --rm -v "${PWD}:/work" -w /work python:3.12-slim sh -lc "pip install -r requirements.txt && python -m bot build-site --output-dir site-test --ratings-file data/test/ratings.tsv --polls-file data/test/polls.tsv"

# 2) Test-Site lokal bereitstellen
docker run --rm -p 8000:8000 -v "${PWD}/site-test:/site" -w /site python:3.12-slim python -m http.server 8000
```

Dann im Browser aufrufen: `http://localhost:8000`

Standardverhalten von `build-site`:
- prüft `polls.tsv` auf neue **finalisierte** Polls
- schreibt nur dann einen neuen Snapshot nach `ratings.tsv`, wenn neue Polls seit dem letzten `calculated_at` vorliegen
- baut danach die statische Seite aus dem aktuellen Stand von `ratings.tsv`

Die erzeugte Seite enthält:
- sortierbare Ranking-Tabelle (inkl. `utility`, `std_error`, `matches`)
- interaktive Episoden-Historie (Linie + Unsicherheitsband)
- leeren Zustand, falls noch keine Ratings vorliegen

Automatisierung:
- Workflow `deploy-pages.yml` läuft bei Push auf `main`
- Deployment wird nur ausgeführt, wenn mindestens ein Ranking vorhanden ist
- Ohne Ranking bleibt der Workflow grün und überspringt den Deploy-Schritt

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

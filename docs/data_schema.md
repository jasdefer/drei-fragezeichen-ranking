# Datenschema – Datenmodell

Dieses Projekt verwendet eine Kombination aus **API-basiertem Datenzugriff** und **TSV-Dateien** (Tab-Separated Values) als persistente, versionierte Datenbasis.

**Episoden-Stammdaten** werden direkt von der [Dreimetadaten API](https://api.dreimetadaten.de/) bezogen.

**TSV-Dateien** werden für projektspezifische Daten verwendet:
- einfache Versionierung über Git
- keine Datenbank-Infrastruktur notwendig
- menschenlesbar und maschinenlesbar
- transparent und nachvollziehbar

---

## Übersicht der Datenstrukturen

Das System besteht aus verschiedenen Datenquellen:

1. **Dreimetadaten API** – Stammdaten der Episoden (extern)
2. **`data/<env>/polls.tsv`** – Umfragedaten und Abstimmungsergebnisse (lokal)
3. **`data/<env>/ratings.tsv`** – Berechnete Bewertungen aus dem Bradley–Terry-Modell (lokal)

`<env>` steht fuer die Datenumgebung, aktuell `prod` oder `test`.

---

## 1. Episoden-Stammdaten (Dreimetadaten API)

**Zweck:**  
Enthält die Grundinformationen zu allen Hörspielfolgen von „Die drei ???".  
Diese Daten werden direkt von der Dreimetadaten API bezogen und nicht lokal gespeichert.

**Zugriff**: Über die Funktionen `fetch_all_episodes()` und `fetch_episode_metadata()` im Modul `bot.dreimetadaten_api`

**Felder (abhängig vom Zugriffspfad):**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `nummer` | Integer | Eindeutige Folgen-Nummer (entspricht der offiziellen Nummerierung) |
| `titel` | String | Titel der Folge (bei Metadaten-Abruf) |
| `beschreibung` | String | Kurzbeschreibung der Handlung (bei Metadaten-Abruf) |
| `urlCoverApple` | String | URL zum Cover-Bild (bei Metadaten-Abruf) |

**Hinweise:**
- Die `nummer` ist der Primärschlüssel und ist eindeutig
- `fetch_all_episodes()` liefert bewusst nur `nummer`
- `fetch_episode_metadata()` liefert zusätzliche Felder (`titel`, `beschreibung`, `urlCoverApple`)
- Daten werden bei jedem Abruf aktuell von der API geladen
- Keine lokale Speicherung erforderlich
- Vollständige Dokumentation siehe `docs/api_usage.md`

---

## 2. `data/<env>/polls.tsv` – Umfragen und Abstimmungsdaten

**Zweck:**  
Dokumentiert alle durchgeführten paarweisen Vergleiche (Polls) zwischen zwei Folgen.  
Jede Zeile repräsentiert eine abgeschlossene Umfrage mit ihren Ergebnissen.

**Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `poll_id` | Integer | Eindeutige ID der Umfrage (fortlaufend) |
| `reddit_post_id` | String | Reddit-Post-ID (zur Nachverfolgung und Verlinkung) |
| `created_at` | ISO 8601 DateTime | Zeitpunkt der Poll-Erstellung (UTC) |
| `closes_at` | ISO 8601 DateTime | Zeitpunkt des automatischen Poll-Schließens (UTC) |
| `episode_a_id` | Integer | ID der ersten verglichenen Folge (Referenz auf API-nummer) |
| `episode_b_id` | Integer | ID der zweiten verglichenen Folge (Referenz auf API-nummer) |
| `votes_a` | Integer | Anzahl der Stimmen für Folge A |
| `votes_b` | Integer | Anzahl der Stimmen für Folge B |
| `finalized_at` | ISO 8601 DateTime | Zeitpunkt der endgültigen Datenerfassung (UTC) |

**Beispiel:**
```
poll_id	reddit_post_id	created_at	closes_at	episode_a_id	episode_b_id	votes_a	votes_b	finalized_at
1	abc123	2024-01-15T10:00:00Z	2024-01-22T10:00:00Z	1	5	42	38	2024-01-22T11:30:00Z
```

**Hinweise:**
- Jede Umfrage vergleicht genau zwei Folgen
- Die Reihenfolge (`episode_a_id` vs. `episode_b_id`) hat keine inhaltliche Bedeutung
- Einträge werden erst nach Abschluss der Umfrage hinzugefügt
- Manuelle Änderungen an abgeschlossenen Polls sind nicht vorgesehen
- Zeitstempel sind immer in UTC im ISO 8601 Format

---

## 3. `data/<env>/ratings.tsv` – Berechnete Bewertungen (Bradley–Terry)

**Zweck:**  
Speichert die aus den Umfragen berechneten **Stärken** (Utilities) jeder Folge **mit vollständiger Historie**.  
Jeder Bradley-Terry-Berechnungslauf schreibt neue Zeilen für alle im Modell berücksichtigten Folgen – es gibt **keine Überschreibungen**.

**Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `episode_id` | Integer | ID der Folge (Referenz auf API-nummer) |
| `utility` | Float | Geschätzte Stärke der Folge im Bradley–Terry-Modell |
| `std_error` | Float | Bootstrap-Standardfehler der Modellschätzung für die Folge |
| `matches` | Integer | Anzahl der Vergleiche, in denen diese Folge beteiligt war |
| `calculated_at` | ISO 8601 DateTime | Zeitpunkt der Berechnung (UTC, z.B. `2026-02-03T14:30:00Z`) |

**Hinweise:**
- Die `utility` ist eine **normierte relative Stärke** mit mean ≈ 1.0 (höherer Wert = präferierter)
- Die Skala basiert auf dem arithmetischen Mittel = 1.0
- `std_error` quantifiziert die Unsicherheit der Schaetzung (kleiner = stabiler)
- `matches` gibt an, wie oft die Folge in Umfragen verglichen wurde
- Folgen mit mehr `matches` haben stabilere `utility`-Werte
- Das Modell berücksichtigt nur Folgen, die über Polls mit Episode `1` verbunden sind
- Diese Datei wird algorithmisch generiert und sollte nicht manuell bearbeitet werden

**Historisierung und Versionierung:**
- Die Datei ist **append-only**: Jeder Berechnungslauf fügt neue Zeilen für alle im Modell berücksichtigten Folgen hinzu
- Der Eintrag mit dem **neuesten `calculated_at`** pro Folge ist das aktuelle Ranking
- Alle älteren Einträge bleiben erhalten und ermöglichen Trend-Analysen
- Bei jedem Bradley-Terry-Lauf werden alle Folgen der aktuell berücksichtigten Zusammenhangskomponente mit dem aktuellen Timestamp versehen
- So ist die komplette Entwicklung des Rankings im Zeitverlauf nachvollziehbar

**Format-Details:**
- utility: 6 Dezimalstellen (z.B. 1.234567)
- std_error: 6 Dezimalstellen (z.B. 0.123456)
- calculated_at: ISO-8601 Format in UTC mit 'Z' Suffix
- Sortierung: nach episode_id aufsteigend pro Berechnungslauf

---

## Trennung der Datenebenen

**Warum API und TSV-Dateien?**

Das Datenmodell trennt bewusst verschiedene logische Ebenen:

### 1. **Stammdaten** (Dreimetadaten API)
- Unveränderliche Referenzdaten von externer Quelle
- Unabhängig von Umfragen
- Immer aktuell, keine lokale Synchronisation notwendig
- Reduziert Wartungsaufwand

### 2. **Transaktionsdaten** (`polls.tsv`)
- Dokumentation aller durchgeführten Vergleiche
- Wächst kontinuierlich mit jeder neuen Umfrage
- Vollständige Historie aller Abstimmungen

### 3. **Modellzustand** (`ratings.tsv`)
- Abgeleitete, berechnete Daten
- **Vollständige Historie** aller Berechnungsläufe (append-only)
- Können jederzeit aus `polls.tsv` neu berechnet werden
- Aktueller Stand = neueste Einträge pro Folge

**Vorteile dieser Trennung:**
- Klare Verantwortlichkeiten
- Keine Datenredundanz
- Einfachere Fehleranalyse
- Modell kann jederzeit neu trainiert werden
- Episoden-Stammdaten sind immer aktuell
- Git-History bleibt übersichtlich (z. B. Transaktions-Änderungen vs. Modell-Updates)

---

## Datenintegrität

**Konsistenzregeln (fachliche Zielregeln):**

1. Alle Episoden-IDs in `polls.tsv` (`episode_a_id`, `episode_b_id`) und `ratings.tsv` (`episode_id`) müssen als `nummer` in der API existieren
2. Jede `poll_id` in `polls.tsv` muss eindeutig sein
3. `episode_a_id` und `episode_b_id` in einem Poll dürfen nicht identisch sein
4. Zeitstempel müssen chronologisch plausibel sein (`closes_at` > `created_at`)
5. Stimmen (`votes_a`, `votes_b`) müssen nicht-negative Ganzzahlen sein

**Aktuell programmatisch validiert (Ist-Stand):**

- Episoden aus der API:
  - `nummer` muss vorhanden, eindeutig und vom Typ Integer sein
- `polls.tsv`:
  - Datei muss existieren
  - Header müssen dem erwarteten Schema und der Reihenfolge entsprechen
- `ratings.tsv`:
  - Datei muss existieren
  - Header müssen dem erwarteten Schema und der Reihenfolge entsprechen
  - `episode_id` muss auf eine vorhandene API-Nummer verweisen
  - `utility` muss als Float parsebar sein
  - `std_error` muss als nicht-negativer Float parsebar sein
  - `matches` muss nicht-negativer Integer sein
  - `calculated_at` muss dem erwarteten UTC-ISO-Format entsprechen (`YYYY-MM-DDTHH:MM:SSZ`)

**Hinweis zur Nutzung:**

Die Validierung kann über den vorhandenen Helper-Aufruf ausgeführt werden:

```bash
python -m bot validate-data
```

**Was aktuell nicht vollständig geprüft wird:**

- Eindeutigkeit von `poll_id` in `polls.tsv`
- Chronologische Plausibilität `created_at < closes_at`
- Vollständige Inhaltsvalidierung aller Poll-Zeilen im Validator

Der Befehl gibt Exit-Code 0 bei Erfolg zurück, andernfalls Exit-Code != 0 mit detaillierten Fehlermeldungen.

---

## Verwendung im Ablauf

### Bereits umgesetzt

1. **Episoden-Metadaten abrufen:**
   - Episoden werden bei Bedarf von der API geladen
   - Keine lokale Stammdaten-Datei notwendig

2. **Poll- und Ratingdateien verwalten:**
   - Poll- und Ratingdaten liegen als TSV-Dateien im Repository
   - `ratings.tsv` wird append-only fortgeschrieben

3. **Ranking berechnen:**
   - Bradley-Terry-Berechnung basiert auf den in `polls.tsv` vorliegenden Daten
   - Ergebnis wird als neuer Zustandsstand in `ratings.tsv` ergänzt

### Geplant

1. **Neue Umfrage erstellen:**
   - Zwei Folgen aus der API auswählen
   - Reddit-Poll posten
   - Metadaten notieren

2. **Umfrage abschließen:**
   - Stimmen auslesen
   - Neue Zeile in `polls.tsv` einfügen
   - Commit erstellen

3. **Ranking aktualisieren:**
   - Bradley–Terry-Modell mit allen Polls aus `polls.tsv` trainieren
   - Neue Zeilen für die aktuell im Modell berücksichtigten Folgen mit aktuellem Timestamp an `ratings.tsv` anhängen
   - Commit erstellen

---

## Arbeiten mit historisierten Ratings

Die `ratings.tsv` speichert die vollständige Historie aller Bradley-Terry-Berechnungen.

### Aktuelles Ranking ermitteln

Das **aktuelle Ranking** ergibt sich aus den Einträgen mit dem jeweils neuesten `calculated_at`-Timestamp pro Folge. Da die Datei alle historischen Berechnungen enthält, muss beim Lesen für jede Folge der Eintrag mit dem maximalen Timestamp ausgewählt werden.

### Zeitliche Entwicklung analysieren

Für Trend-Analysen stehen alle Einträge einer Folge zur Verfügung und können chronologisch nach `calculated_at` sortiert werden. Dadurch lässt sich die Entwicklung von `utility`, `std_error` und `matches` im Zeitverlauf nachvollziehen.

### Empfehlungen

- Beim Lesen der Datei immer den **neuesten Timestamp** für das aktuelle Ranking verwenden
- Historische Daten nicht löschen (wichtig für Reproduzierbarkeit)
- Neue Bradley-Terry-Läufe fügen alle aktuell im Modell berücksichtigten Folgen mit identischem `calculated_at` hinzu
- Dadurch bleiben Zustandsstände konsistent und vergleichbar

---

## Datentypen und Formatierung

- **Integer:** Ganzzahlen ohne Anführungszeichen
- **Float:** Dezimalzahlen mit Punkt als Trennzeichen (nicht Komma)
- **String:** Text ohne Anführungszeichen (TSV-Spalten sind durch Tabs getrennt)
- **DateTime:** ISO 8601 Format in UTC: `YYYY-MM-DDTHH:MM:SSZ`
- **Trennzeichen:** Tab-Zeichen (`\t`), keine Leerzeichen
- **Zeilenende:** Unix-Style (`\n`)
- **Kodierung:** UTF-8

---

## Erweiterbarkeit

Das Schema ist bewusst minimalistisch gehalten, kann aber bei Bedarf erweitert werden:

**Mögliche Erweiterungen:**
- Zusätzliche Metadaten in `episodes.tsv` (z. B. Autoren, Länge, Themen)
- Mehrere Modelltypen parallel in separaten `ratings_*.tsv`-Dateien
- Tracking von Poll-Quellen (z. B. mehrere Communities)

Bei Erweiterungen sollte die Trennung von Stammdaten, Transaktionen und Modellzustand beibehalten werden.

---

## Zusammenfassung

Dieses hybride Datenmodell bietet:
- ✅ Einfachheit und Transparenz
- ✅ Volle Versionskontrolle über Git (für lokale Daten)
- ✅ Keine externen Datenbank-Abhängigkeiten
- ✅ Klare Trennung von Daten-Ebenen
- ✅ Reproduzierbarkeit und Nachvollziehbarkeit
- ✅ Langfristige Wartbarkeit
- ✅ Immer aktuelle Episoden-Stammdaten von der API

Alle Änderungen an den lokalen Daten sind über die Git-Historie vollständig nachvollziehbar.
Episoden-Stammdaten werden stets aktuell von der Dreimetadaten API bezogen.

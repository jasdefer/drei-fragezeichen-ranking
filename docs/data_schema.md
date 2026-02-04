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
2. **`data/polls.tsv`** – Umfragedaten und Abstimmungsergebnisse (lokal)
3. **`data/ratings.tsv`** – Berechnete Bewertungen aus dem Bradley–Terry-Modell (lokal)

---

## 1. Episoden-Stammdaten (Dreimetadaten API)

**Zweck:**  
Enthält die Grundinformationen zu allen Hörspielfolgen von „Die drei ???".  
Diese Daten werden direkt von der Dreimetadaten API bezogen und nicht lokal gespeichert.

**Zugriff:**  
```python
from bot.dreimetadaten_api import fetch_all_episodes, fetch_episode_metadata

# Alle Episoden laden
episodes = fetch_all_episodes()

# Spezifische Episode laden
episode = fetch_episode_metadata(149)
```

**Felder:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `nummer` | Integer | Eindeutige Folgen-Nummer (entspricht der offiziellen Nummerierung) |
| `titel` | String | Titel der Folge |
| `beschreibung` | String | Kurzbeschreibung der Handlung |
| `urlCoverApple` | String | URL zum Cover-Bild |

**Beispiel:**
```json
{
  "nummer": 149,
  "titel": "...und die feurige Flut",
  "beschreibung": "Eine mysteriöse Feuersbrunst bedroht die Stadt",
  "urlCoverApple": "https://..."
}
```

**Hinweise:**
- Die `nummer` ist der Primärschlüssel und ist eindeutig
- Daten werden bei jedem Abruf aktuell von der API geladen
- Keine lokale Speicherung erforderlich
- Vollständige Dokumentation siehe `docs/api_usage.md`

---

## 2. `data/polls.tsv` – Umfragen und Abstimmungsdaten

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

## 3. `data/ratings.tsv` – Berechnete Bewertungen (Bradley–Terry)

**Zweck:**  
Speichert die aus den Umfragen berechneten **Stärken** (Utilities) jeder Folge **mit vollständiger Historie**.  
Jeder Bradley-Terry-Berechnungslauf schreibt neue Zeilen für alle Folgen – es gibt **keine Überschreibungen**.

**Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `episode_id` | Integer | ID der Folge (Referenz auf API-nummer) |
| `utility` | Float | Geschätzte Stärke der Folge im Bradley–Terry-Modell |
| `matches` | Integer | Anzahl der Vergleiche, in denen diese Folge beteiligt war |
| `calculated_at` | ISO 8601 DateTime | Zeitpunkt der Berechnung (UTC, z.B. `2026-02-03T14:30:00Z`) |

**Beispiel:**
```
episode_id	utility	matches	calculated_at
1	1.23	5	2026-01-15T10:00:00Z
5	0.87	5	2026-01-15T10:00:00Z
1	1.45	8	2026-01-22T11:30:00Z
5	0.92	8	2026-01-22T11:30:00Z
```

**Hinweise:**
- Die `utility` ist eine **relative Stärke** (höherer Wert = präferierter)
- Die Skala ist nicht absolut und kann sich mit neuen Daten verschieben
- `matches` gibt an, wie oft die Folge in Umfragen verglichen wurde
- Folgen mit mehr `matches` haben stabilere `utility`-Werte
- Diese Datei wird algorithmisch generiert und sollte nicht manuell bearbeitet werden

**Historisierung und Versionierung:**
- Die Datei ist **append-only**: Jeder Berechnungslauf fügt neue Zeilen für alle Folgen hinzu
- Der Eintrag mit dem **neuesten `calculated_at`** pro Folge ist das aktuelle Ranking
- Alle älteren Einträge bleiben erhalten und ermöglichen Trend-Analysen
- Bei jedem Bradley-Terry-Lauf werden **alle Folgen** mit dem aktuellen Timestamp versehen
- So ist die komplette Entwicklung des Rankings im Zeitverlauf nachvollziehbar

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

**Konsistenzregeln:**

1. Alle `episode_id` in `polls.tsv` und `ratings.tsv` müssen als `nummer` in der API existieren
2. Jede `poll_id` in `polls.tsv` muss eindeutig sein
3. `episode_a_id` und `episode_b_id` in einem Poll dürfen nicht identisch sein
4. Zeitstempel müssen chronologisch plausibel sein (`closes_at` > `created_at`)
5. Stimmen (`votes_a`, `votes_b`) müssen nicht-negative Ganzzahlen sein

**Validierung:**  
Diese Regeln werden programmatisch überprüft. Nutze den Befehl:

```bash
python -m bot validate-data
```

**Was wird validiert:**

- **Episoden** (von API):
  - `nummer` muss eindeutig sein
  - `titel` darf nicht leer sein
  
- **`polls.tsv`**:
  - Datei muss existieren
  - Header müssen dem erwarteten Schema entsprechen (Spaltennamen und Reihenfolge)
  - Es ist erlaubt, dass keine Datenzeilen existieren

Der Befehl gibt Exit-Code 0 bei Erfolg zurück, andernfalls Exit-Code != 0 mit detaillierten Fehlermeldungen.

---

## Verwendung im Workflow

1. **Episoden-Metadaten abrufen:**
   - Episoden werden bei Bedarf von der API geladen
   - Keine lokale Datei notwendig

2. **Neue Umfrage erstellen:**
   - Zwei Folgen aus der API auswählen
   - Reddit-Poll posten
   - Metadaten notieren

3. **Umfrage abschließen:**
   - Stimmen auslesen
   - Neue Zeile in `polls.tsv` einfügen
   - Commit erstellen

4. **Ranking aktualisieren:**
   - Bradley–Terry-Modell mit allen Polls aus `polls.tsv` trainieren
   - Neue Zeilen für **alle Folgen** mit aktuellem Timestamp an `ratings.tsv` anhängen
   - Commit erstellen

---

## Arbeiten mit historisierten Ratings

Die `ratings.tsv` speichert die vollständige Historie aller Bradley-Terry-Berechnungen.

### Aktuelles Ranking ermitteln

Das **aktuelle Ranking** ergibt sich aus den Einträgen mit dem jeweils neuesten `calculated_at`-Timestamp pro Folge. Da die Datei alle historischen Berechnungen enthält, muss beim Lesen für jede Folge der Eintrag mit dem maximalen Timestamp ausgewählt werden.

### Zeitliche Entwicklung analysieren

Für Trend-Analysen stehen alle Einträge einer Folge zur Verfügung und können chronologisch nach `calculated_at` sortiert werden. Dadurch lässt sich die Entwicklung der `utility`-Werte und der Anzahl der `matches` im Zeitverlauf nachvollziehen.

### Best Practices

- Beim Lesen der Datei immer den **neuesten Timestamp** für das aktuelle Ranking verwenden
- Historische Daten nicht löschen (wichtig für Reproduzierbarkeit)
- Neue Bradley-Terry-Läufe fügen **alle Folgen** mit identischem `calculated_at` hinzu
- Dadurch bleiben Snapshots konsistent und vergleichbar

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

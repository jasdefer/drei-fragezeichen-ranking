# Datenschema – TSV-Datenmodell

Dieses Projekt verwendet **TSV-Dateien** (Tab-Separated Values) als persistente, versionierte Datenbasis.

TSVs bieten:
- einfache Versionierung über Git
- keine Datenbank-Infrastruktur notwendig
- menschenlesbar und maschinenlesbar
- transparent und nachvollziehbar

---

## Übersicht der Datenstrukturen

Das System besteht aus drei separaten TSV-Dateien, die unterschiedliche Aspekte der Daten abbilden:

1. **`data/episodes.tsv`** – Stammdaten der Episoden
2. **`data/polls.tsv`** – Umfragedaten und Abstimmungsergebnisse
3. **`data/ratings.tsv`** – Berechnete Bewertungen aus dem Bradley–Terry-Modell

---

## 1. `data/episodes.tsv` – Episoden-Stammdaten

**Zweck:**  
Enthält die Grundinformationen zu allen Hörspielfolgen von „Die drei ???".  
Diese Daten ändern sich nicht durch Umfragen und dienen als Referenz.

**Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `episode_id` | Integer | Eindeutige Folgen-Nummer (entspricht der offiziellen Nummerierung) |
| `title` | String | Titel der Folge (ohne vorangestellte Nummerierung) |
| `year` | Integer | Erscheinungsjahr des Hörspiels |
| `type` | String | Typ der Folge: `regular` (normale Folge) oder `special` (Sonderfolge) |
| `description` | String | Optionale Kurzbeschreibung der Handlung |

**Beispiel:**
```
episode_id	title	year	type	description
1	...und der Super-Papagei	1979	regular	Die drei Detektive auf der Spur eines sprechenden Papageis
```

**Hinweise:**
- Die `episode_id` ist der Primärschlüssel und muss eindeutig sein
- Neue Folgen werden am Ende angefügt
- Bestehende Einträge sollten nicht verändert werden (außer bei Fehlerkorrekturen)
- Fehlende Beschreibungen sind erlaubt (leeres Feld)

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
| `episode_a_id` | Integer | ID der ersten verglichenen Folge (Referenz auf `episodes.tsv`) |
| `episode_b_id` | Integer | ID der zweiten verglichenen Folge (Referenz auf `episodes.tsv`) |
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
Speichert die aus den Umfragen berechneten **Stärken** (Utilities) jeder Folge.  
Diese Werte werden nach jeder neuen Umfrage aktualisiert.

**Spalten:**

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `episode_id` | Integer | ID der Folge (Referenz auf `episodes.tsv`) |
| `utility` | Float | Geschätzte Stärke der Folge im Bradley–Terry-Modell |
| `matches` | Integer | Anzahl der Vergleiche, in denen diese Folge beteiligt war |

**Beispiel:**
```
episode_id	utility	matches
1	1.23	5
5	0.87	5
```

**Hinweise:**
- Die `utility` ist eine **relative Stärke** (höherer Wert = präferierter)
- Die Skala ist nicht absolut und kann sich mit neuen Daten verschieben
- `matches` gibt an, wie oft die Folge in Umfragen verglichen wurde
- Folgen mit mehr `matches` haben stabilere `utility`-Werte
- Diese Datei wird algorithmisch generiert und sollte nicht manuell bearbeitet werden

---

## Trennung der Datenebenen

**Warum drei separate Dateien?**

Das Datenmodell trennt bewusst drei logische Ebenen:

### 1. **Stammdaten** (`episodes.tsv`)
- Unveränderliche Referenzdaten
- Unabhängig von Umfragen
- Wächst langsam (neue Folgen werden selten hinzugefügt)

### 2. **Transaktionsdaten** (`polls.tsv`)
- Dokumentation aller durchgeführten Vergleiche
- Wächst kontinuierlich mit jeder neuen Umfrage
- Vollständige Historie aller Abstimmungen

### 3. **Modellzustand** (`ratings.tsv`)
- Abgeleitete, berechnete Daten
- Ändern sich mit jeder neuen Umfrage
- Können jederzeit aus `polls.tsv` neu berechnet werden

**Vorteile dieser Trennung:**
- Klare Verantwortlichkeiten
- Keine Datenredundanz
- Einfachere Fehleranalyse
- Modell kann jederzeit neu trainiert werden
- Git-History bleibt übersichtlich (z. B. Stammdaten-Änderungen vs. Modell-Updates)

---

## Datenintegrität

**Konsistenzregeln:**

1. Alle `episode_id` in `polls.tsv` und `ratings.tsv` müssen in `episodes.tsv` existieren
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

- `episodes.tsv`:
  - `episode_id` muss eindeutig sein
  - `title` darf nicht leer sein
  - `year` ist optional, aber falls gesetzt: ganzzahlig und im Bereich 1900–2100
  - `type` muss entweder `regular` oder `special` sein
  
- `polls.tsv`:
  - Datei muss existieren
  - Header müssen dem erwarteten Schema entsprechen (Spaltennamen und Reihenfolge)
  - Es ist erlaubt, dass keine Datenzeilen existieren

Der Befehl gibt Exit-Code 0 bei Erfolg zurück, andernfalls Exit-Code != 0 mit detaillierten Fehlermeldungen.

---

## Verwendung im Workflow

1. **Neue Umfrage erstellen:**
   - Zwei Folgen aus `episodes.tsv` auswählen
   - Reddit-Poll posten
   - Metadaten notieren

2. **Umfrage abschließen:**
   - Stimmen auslesen
   - Neue Zeile in `polls.tsv` einfügen
   - Commit erstellen

3. **Ranking aktualisieren:**
   - Bradley–Terry-Modell mit allen Polls aus `polls.tsv` trainieren
   - `ratings.tsv` vollständig neu schreiben
   - Commit erstellen

4. **Neue Folgen hinzufügen:**
   - Neue Zeile in `episodes.tsv` einfügen
   - Commit erstellen
   - Folge steht für zukünftige Polls zur Verfügung

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
- Historisierung der Ratings über Zeit
- Tracking von Poll-Quellen (z. B. mehrere Communities)

Bei Erweiterungen sollte die Trennung von Stammdaten, Transaktionen und Modellzustand beibehalten werden.

---

## Zusammenfassung

Dieses TSV-basierte Datenmodell bietet:
- ✅ Einfachheit und Transparenz
- ✅ Volle Versionskontrolle über Git
- ✅ Keine externen Datenbank-Abhängigkeiten
- ✅ Klare Trennung von Daten-Ebenen
- ✅ Reproduzierbarkeit und Nachvollziehbarkeit
- ✅ Langfristige Wartbarkeit

Alle Änderungen an den Daten sind über die Git-Historie vollständig nachvollziehbar.

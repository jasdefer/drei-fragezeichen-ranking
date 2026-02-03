# Daten-Verzeichnis / Data Directory

## Episoden-Daten (episodes.tsv)

### ⚠️ Wichtiger Hinweis zur Datenqualität

Die aktuellen Episode-Daten in `episodes.tsv` wurden **ohne direkten Zugriff** auf die offizielle Quelle (https://www.rocky-beach.com/php/wordpress/) erstellt. 

**Bekannte Einschränkungen:**
- Einige Episodentitel können ungenau oder vereinfacht sein
- Es existieren Duplikate bei Titeln (21 Duplikat-Gruppen identifiziert)
- Erscheinungsjahre basieren auf Schätzungen für neuere Episoden
- Keine Sonderfolgen (type: "special") wurden hinzugefügt

### ✅ Was funktioniert

- **Format**: TSV-Datei entspricht dem Schema in `docs/data_schema.md`
- **Validierung**: Alle 220 Episoden bestehen die Schema-Validierung (`python -m bot validate-data`)
- **Struktur**: Korrekte Spalten (episode_id, title, year, type, description)
- **Basis für Ranking**: Die Daten können als Ausgangspunkt für das Community-Ranking dienen

### 🔄 Nächste Schritte zur Verbesserung

1. **Manuelle Verifizierung** mit rocky-beach.com:
   - Episodentitel korrigieren
   - Duplikate auflösen
   - Fehlende Episoden ergänzen
   - Sonderfolgen hinzufügen

2. **Automatisierte Aktualisierung** implementieren (wie im Issue erwähnt):
   - Script zum Abrufen neuer Episoden
   - Regelmäßige Synchronisation mit offizieller Quelle

3. **Community-Beiträge**:
   - Pull Requests mit Korrekturen sind willkommen
   - Besonders für Fans der Serie, die die genauen Titel kennen

### Duplikate-Liste

Die folgenden Episodentitel erscheinen mehrfach in der Datei:
- "...und der Fluch des Rubins" (Episoden 5, 125, 217)
- "...und der Fluch des Drachen" (Episoden 97, 128, 188)
- "...und der verschollene Pilot" (Episoden 163, 176, 185)
- ... und 18 weitere Duplikat-Gruppen

Siehe `data/episodes.tsv` für die vollständige Liste.

### Verwendung trotz Einschränkungen

Die Daten sind **verwendbar** für:
- ✅ Entwicklung und Testing des Ranking-Systems
- ✅ Proof-of-Concept für paarweise Vergleiche
- ✅ Community-Umfragen (Benutzer können bei Bedarf Titel klären)
- ✅ Grundlage für spätere Verfeinerung

Die Daten sind **nicht optimal** für:
- ❌ Offizielle Publikation ohne Verifizierung
- ❌ Genaue historische Referenzen
- ❌ Automatisierte Systeme, die exakte Titel benötigen

## Weitere Dateien

- `polls.tsv`: Umfragen-Daten (derzeit leer)
- `ratings.tsv`: Bradley-Terry Bewertungen (derzeit leer)

Siehe `docs/data_schema.md` für Details zum Datenmodell.

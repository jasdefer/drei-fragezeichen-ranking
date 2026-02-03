# Daten-Verzeichnis / Data Directory

## Episoden-Daten (episodes.tsv)

### ✅ Aktueller Stand

Die Datei `episodes.tsv` enthält **220 Episoden** (Folgen 1-220) der "Die drei ???" Hörspielreihe.

**Status:**
- **Format**: TSV-Datei entspricht dem Schema in `docs/data_schema.md` ✓
- **Validierung**: Alle 220 Episoden bestehen die Schema-Validierung (`python -m bot validate-data`) ✓
- **Datenqualität**: 
  - Episoden 1-100: Verifizierte, korrekte Daten vom Repository-Maintainer ✓
  - Episoden 101-220: Zusammengetragen aus verschiedenen Quellen
- **Struktur**: Korrekte Spalten (episode_id, title, year, type, description) ✓

### 🔄 Nächste Schritte

1. **Datenverifizierung**:
   - Episoden 101-220 sollten mit der offiziellen Quelle (https://www.rocky-beach.com/php/wordpress/) abgeglichen werden
   - Korrekturen bei Titel, Jahr oder Beschreibung vornehmen falls nötig
   - Sonderfolgen (type: "special") identifizieren und hinzufügen

2. **Automatisierte Aktualisierung** implementieren (wie im Issue erwähnt):
   - Script zum Abrufen neuer Episoden von rocky-beach.com
   - Regelmäßige Synchronisation mit offizieller Quelle

3. **Community-Beiträge**:
   - Pull Requests mit Korrekturen sind willkommen
   - Besonders für Fans der Serie, die die genauen Episodendetails kennen

### Verwendung

Die aktuellen 220 Episoden sind **verwendbar** für:
- ✅ Community-Ranking mit paarweisen Vergleichen
- ✅ Reddit-Umfragen
- ✅ Entwicklung und Testing des Ranking-Systems
- ✅ Grundlage für weitere Verfeinerungen

## Weitere Dateien

- `polls.tsv`: Umfragen-Daten (derzeit leer)
- `ratings.tsv`: Bradley-Terry Bewertungen (derzeit leer)

Siehe `docs/data_schema.md` für Details zum Datenmodell.

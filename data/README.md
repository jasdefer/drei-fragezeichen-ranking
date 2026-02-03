# Daten-Verzeichnis / Data Directory

## Episoden-Daten (episodes.tsv)

### ✅ Aktueller Stand

Die Datei `episodes.tsv` enthält **50 verifizierte Episoden** (Folgen 1-50) der "Die drei ???" Hörspielreihe.

**Status:**
- **Format**: TSV-Datei entspricht dem Schema in `docs/data_schema.md` ✓
- **Validierung**: Alle 50 Episoden bestehen die Schema-Validierung (`python -m bot validate-data`) ✓
- **Datenqualität**: Verifizierte, korrekte Daten für Episoden 1-50 ✓
- **Struktur**: Korrekte Spalten (episode_id, title, year, type, description) ✓

### 🔄 Nächste Schritte

1. **Weitere Episoden hinzufügen**:
   - Episoden 51 und höher müssen noch mit korrekten Daten aus der offiziellen Quelle (https://www.rocky-beach.com/php/wordpress/) ergänzt werden
   - Sonderfolgen (type: "special") identifizieren und hinzufügen

2. **Automatisierte Aktualisierung** implementieren (wie im Issue erwähnt):
   - Script zum Abrufen neuer Episoden von rocky-beach.com
   - Regelmäßige Synchronisation mit offizieller Quelle

3. **Community-Beiträge**:
   - Pull Requests mit weiteren verifizierten Episoden sind willkommen
   - Besonders für Fans der Serie, die Zugriff auf vollständige Episodenlisten haben

### Verwendung

Die aktuellen 50 Episoden sind **produktionsbereit** für:
- ✅ Community-Ranking mit paarweisen Vergleichen
- ✅ Reddit-Umfragen
- ✅ Entwicklung und Testing des Ranking-Systems
- ✅ Offizielle Publikation

## Weitere Dateien

- `polls.tsv`: Umfragen-Daten (derzeit leer)
- `ratings.tsv`: Bradley-Terry Bewertungen (derzeit leer)

Siehe `docs/data_schema.md` für Details zum Datenmodell.

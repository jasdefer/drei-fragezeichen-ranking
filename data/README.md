# Datenumgebungen

- `data/prod/`: Produktionsdaten fuer regulaeren Betrieb und GitHub Pages Deploy auf `main`
- `data/test/`: Synthetische Testdaten fuer Entwicklung und PR-Preview-Artefakte

Beide Umgebungen nutzen dasselbe TSV-Schema.

## Wichtige Hinweise

- `ratings.tsv` ist append-only.
- `build-site` aktualisiert `ratings.tsv` nur, wenn neue finalisierte Polls vorliegen.
- Lokale Builds sollten `--ratings-file` und `--polls-file` explizit setzen, wenn nicht mit den Production-Defaults gearbeitet wird.

#!/usr/bin/env python3
"""
Beispiel-Skript für Bradley-Terry Rating-Berechnung

Demonstriert die Verwendung des Bradley-Terry-Moduls mit Beispieldaten.
Kann auch als Basis für GitHub Actions oder Bot-Integration verwendet werden.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Füge bot-Modul zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from bot.bradley_terry import run_rating_update
from bot.logger import setup_logging
import logging


def main():
    """
    Hauptfunktion: Führt Bradley-Terry Rating-Update durch.
    
    Returns:
        0 bei Erfolg, 1 bei Fehler
    """
    # Setup logging
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Pfade
    repo_root = Path(__file__).parent
    polls_path = repo_root / "data" / "polls.tsv"
    ratings_path = repo_root / "data" / "ratings.tsv"
    
    logger.info("=" * 60)
    logger.info("Bradley-Terry Rating-Berechnung")
    logger.info("=" * 60)
    logger.info(f"Polls-Datei: {polls_path}")
    logger.info(f"Ratings-Datei: {ratings_path}")
    logger.info("")
    
    # Prüfe ob polls.tsv existiert
    if not polls_path.exists():
        logger.error(f"Fehler: {polls_path} existiert nicht!")
        return 1
    
    # Führe Rating-Update durch
    try:
        run_rating_update(polls_path, ratings_path)
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Rating-Update erfolgreich abgeschlossen!")
        logger.info("=" * 60)
        
        # Zeige Anzahl der geschriebenen Zeilen
        if ratings_path.exists():
            with open(ratings_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Zähle nur Datenzeilen (ohne Header)
                data_lines = [l for l in lines if not l.startswith('episode_id')]
                logger.info(f"Ratings-Datei enthält {len(data_lines)} Einträge")
        
        return 0
        
    except Exception as e:
        logger.error("")
        logger.error("=" * 60)
        logger.error(f"❌ Fehler beim Rating-Update: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

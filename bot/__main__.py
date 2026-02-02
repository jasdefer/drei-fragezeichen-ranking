"""
Haupteinstiegspunkt für den Bot

Dieses Modul ermöglicht die Ausführung des Bots via:
    python -m bot

Vorerst wird nur eine Statusmeldung ausgegeben.
Reddit-Funktionalität wird in späteren Issues implementiert.
"""

import sys
from bot.logger import setup_logging, get_logger


def main():
    """
    Hauptfunktion des Bots
    
    Führt die Bot-Logik aus. Aktuell nur ein Smoke Test ohne
    tatsächliche Reddit-Funktionalität.
    """
    # Logging initialisieren
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("Drei ??? Community Ranking Bot")
    logger.info("=" * 60)
    logger.info("Bot gestartet")
    logger.info("Python-Version: %s", sys.version.split()[0])
    logger.info("Abhängigkeiten bereit:")
    
    # Überprüfen, ob kritische Abhängigkeiten importierbar sind
    try:
        import praw
        logger.info("  - praw: %s", praw.__version__)
    except ImportError:
        logger.warning("  - praw: nicht installiert")
    
    try:
        import dateutil
        logger.info("  - python-dateutil: installiert")
    except ImportError:
        logger.warning("  - python-dateutil: nicht installiert")
    
    logger.info("=" * 60)
    logger.info("Status: Bereit (keine Aktionen definiert)")
    logger.info("=" * 60)
    
    # Erfolgreicher Exit
    return 0


if __name__ == "__main__":
    sys.exit(main())

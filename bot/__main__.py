"""
Haupteinstiegspunkt für den Bot

Dieses Modul ermöglicht die Ausführung des Bots via:
    python -m bot [command]

Verfügbare Befehle:
    validate-data: Validiert die TSV-Dateien in data/
"""

import sys
import argparse
from pathlib import Path
from bot.logger import setup_logging, get_logger
from bot.tsv_loader import load_episodes, load_polls, TSVLoadError
from bot.validator import validate_episodes, validate_polls_schema, ValidationError


def validate_data() -> int:
    """
    Validiert die TSV-Dateien (episodes.tsv und polls.tsv).
    
    Returns:
        Exit-Code: 0 bei Erfolg, 1 bei Fehler
    """
    logger = get_logger(__name__)
    
    # Pfade zu den Datendateien
    data_dir = Path(__file__).parent.parent / "data"
    episodes_file = data_dir / "episodes.tsv"
    polls_file = data_dir / "polls.tsv"
    
    try:
        logger.info("Starte Datenvalidierung...")
        logger.info("=" * 60)
        
        # Episodes laden und validieren
        logger.info("Lade episodes.tsv...")
        episodes = load_episodes(episodes_file)
        
        logger.info("Validiere Episoden...")
        validate_episodes(episodes)
        
        # Polls laden und Schema validieren
        logger.info("Lade polls.tsv...")
        polls = load_polls(polls_file)
        
        logger.info("Validiere Polls-Schema...")
        validate_polls_schema(polls)
        
        logger.info("=" * 60)
        logger.info("✓ Validierung erfolgreich abgeschlossen")
        logger.info(f"  - {len(episodes)} Episoden validiert")
        logger.info(f"  - {len(polls)} Polls geladen (Schema korrekt)")
        logger.info("=" * 60)
        
        return 0
        
    except (TSVLoadError, ValidationError) as e:
        logger.error("=" * 60)
        logger.error("✗ Validierung fehlgeschlagen")
        logger.error(str(e))
        logger.error("=" * 60)
        return 1
    except Exception as e:
        logger.error("=" * 60)
        logger.error("✗ Unerwarteter Fehler während der Validierung")
        logger.error(str(e))
        logger.error("=" * 60)
        return 1


def show_status() -> int:
    """
    Zeigt den Bot-Status an (ursprüngliche Funktion).
    
    Returns:
        Exit-Code: 0 bei Erfolg
    """
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
    logger.info("Status: Bereit")
    logger.info("Nutze 'python -m bot validate-data' zur Datenvalidierung")
    logger.info("=" * 60)
    
    return 0


def main():
    """
    Hauptfunktion des Bots
    
    Parst Kommandozeilenargumente und führt entsprechende Befehle aus.
    """
    # Logging initialisieren
    setup_logging()
    
    # Argument-Parser erstellen
    parser = argparse.ArgumentParser(
        description="Drei ??? Community Ranking Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        choices=['validate-data'],
        help='Auszuführender Befehl (optional)'
    )
    
    args = parser.parse_args()
    
    # Befehl ausführen
    if args.command == 'validate-data':
        return validate_data()
    else:
        return show_status()


if __name__ == "__main__":
    sys.exit(main())

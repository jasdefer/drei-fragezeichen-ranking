"""
Haupteinstiegspunkt für den Bot

Dieses Modul ermöglicht die Ausführung des Bots via:
    python -m bot [command]

Verfügbare Befehle:
    validate-data: Validiert die API-Daten (Episoden) und TSV-Dateien (Polls, Ratings)
    build-site: Aktualisiert optional ratings.tsv aus Polls und baut statische Visualisierung
"""

import sys
import argparse
from pathlib import Path

from bot.logger import setup_logging, get_logger
from bot.tsv_repository import load_polls, load_ratings, TSVLoadError
from bot.dreimetadaten_api import fetch_all_episodes, APIError
from bot.validator import validate_episodes, validate_polls_schema, validate_ratings, ValidationError
from bot.visualization import build_visualization_site, VisualizationError


def validate_data() -> int:
    """
    Validiert die API-Daten (Episoden) und TSV-Dateien (polls.tsv und ratings.tsv).
    
    Returns:
        Exit-Code: 0 bei Erfolg, 1 bei Fehler
    """
    logger = get_logger(__name__)
    
    # Pfade zu den Datendateien (Production)
    data_dir = Path(__file__).parent.parent / "data" / "prod"
    polls_file = data_dir / "polls.tsv"
    ratings_file = data_dir / "ratings.tsv"
    
    try:
        logger.info("Starte Datenvalidierung...")
        logger.info("=" * 60)
        
        # Episodes von der API laden und validieren
        logger.info("Lade Episoden von der Dreimetadaten API...")
        episodes = fetch_all_episodes()
        
        logger.info("Validiere Episoden...")
        validate_episodes(episodes)
        
        # Polls laden und Schema validieren
        logger.info("Lade polls.tsv...")
        polls = load_polls(polls_file)
        
        logger.info("Validiere Polls-Schema...")
        validate_polls_schema(polls)
        
        # Ratings laden und validieren
        logger.info("Lade ratings.tsv...")
        ratings = load_ratings(ratings_file)
        
        logger.info("Validiere Ratings...")
        validate_ratings(ratings, episodes)
        
        logger.info("=" * 60)
        logger.info("✓ Validierung erfolgreich abgeschlossen")
        logger.info(f"  - {len(episodes)} Episoden validiert (von API)")
        logger.info(f"  - {len(polls)} Polls geladen (Schema korrekt)")
        logger.info(f"  - {len(ratings)} Ratings validiert")
        logger.info("=" * 60)
        
        return 0
        
    except (TSVLoadError, ValidationError, APIError) as e:
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


def build_site(
    output_dir: Path,
    ratings_file: Path,
    polls_file: Path,
    update_ratings_from_polls: bool,
    site_variant: str,
) -> int:
    """
    Erstellt die statische Visualisierungsseite aus ratings.tsv.

    Args:
        output_dir: Zielordner fuer die generierte Seite
        ratings_file: Pfad zur ratings.tsv
        polls_file: Pfad zur polls.tsv
        update_ratings_from_polls: ratings.tsv vor Build aus Polls aktualisieren
        site_variant: Zielvariante der generierten Seite (prod/test)

    Returns:
        Exit-Code: 0 bei Erfolg, 1 bei Fehler
    """
    logger = get_logger(__name__)

    try:
        logger.info("Starte Build der Visualisierungsseite...")
        build_visualization_site(
            ratings_file=ratings_file,
            output_dir=output_dir,
            polls_file=polls_file,
            update_ratings_from_polls=update_ratings_from_polls,
            site_variant=site_variant,
        )
        logger.info("Visualisierung erfolgreich gebaut in: %s", output_dir)
        return 0
    except (VisualizationError, TSVLoadError) as e:
        logger.error("Build der Visualisierungsseite fehlgeschlagen: %s", e)
        return 1
    except Exception as e:
        logger.error("Unerwarteter Fehler beim Build der Visualisierung: %s", e)
        return 1


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
        choices=['validate-data', 'build-site'],
        help='Auszufuehrender Befehl (optional)'
    )

    default_data_dir = Path(__file__).parent.parent / "data" / "prod"
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).parent.parent / "site",
        help='Zielordner fuer generierte Webseite (nur bei build-site)'
    )
    parser.add_argument(
        '--ratings-file',
        type=Path,
        default=default_data_dir / "ratings.tsv",
        help='Pfad zur ratings.tsv (nur bei build-site)'
    )
    parser.add_argument(
        '--polls-file',
        type=Path,
        default=default_data_dir / "polls.tsv",
        help='Pfad zur polls.tsv (nur bei build-site)'
    )
    parser.add_argument(
        '--skip-ratings-update',
        action='store_true',
        help='Ueberspringt Polls->Ratings Update vor build-site'
    )
    parser.add_argument(
        '--site-variant',
        choices=['prod', 'test'],
        default='prod',
        help='Markiert die Ausgabe als prod- oder test-Dashboard (nur bei build-site)'
    )
    
    args = parser.parse_args()
    
    # Befehl ausführen
    if args.command == 'validate-data':
        return validate_data()
    elif args.command == 'build-site':
        return build_site(
            output_dir=args.output_dir,
            ratings_file=args.ratings_file,
            polls_file=args.polls_file,
            update_ratings_from_polls=(not args.skip_ratings_update),
            site_variant=args.site_variant,
        )
    else:
        return show_status()


if __name__ == "__main__":
    sys.exit(main())

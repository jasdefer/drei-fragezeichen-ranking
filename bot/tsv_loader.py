"""
TSV Datei-Loader

Dieses Modul stellt Funktionen zum Laden und Parsen von TSV-Dateien bereit.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from bot.logger import get_logger

logger = get_logger(__name__)


class TSVLoadError(Exception):
    """Exception für TSV-Ladefehler"""
    pass


def load_tsv(file_path: Path) -> List[Dict[str, str]]:
    """
    Lädt eine TSV-Datei und gibt eine Liste von Dictionaries zurück.
    
    Args:
        file_path: Pfad zur TSV-Datei
        
    Returns:
        Liste von Dictionaries, wobei jeder Key ein Spaltenname ist
        
    Raises:
        TSVLoadError: Wenn die Datei nicht geladen werden kann
    """
    if not file_path.exists():
        raise TSVLoadError(f"Datei nicht gefunden: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            # Prüfen, ob Header vorhanden ist
            if reader.fieldnames is None:
                raise TSVLoadError(f"Keine Header-Zeile gefunden in {file_path}")
            
            data = list(reader)
            logger.debug(f"TSV-Datei geladen: {file_path} ({len(data)} Zeilen)")
            return data
            
    except csv.Error as e:
        raise TSVLoadError(f"Fehler beim Parsen der TSV-Datei {file_path}: {e}")
    except Exception as e:
        raise TSVLoadError(f"Fehler beim Laden der Datei {file_path}: {e}")


def load_episodes(file_path: Path) -> List[Dict[str, str]]:
    """
    Lädt die episodes.tsv Datei.
    
    Args:
        file_path: Pfad zur episodes.tsv
        
    Returns:
        Liste von Episode-Dictionaries
        
    Raises:
        TSVLoadError: Wenn die Datei nicht geladen werden kann oder Header fehlen
    """
    data = load_tsv(file_path)
    
    # Erwartete Header prüfen
    expected_headers = {'episode_id', 'title', 'year', 'type', 'description'}
    
    if not data:
        logger.warning(f"Keine Episoden in {file_path} gefunden")
        return []
    
    actual_headers = set(data[0].keys())
    
    if not expected_headers.issubset(actual_headers):
        missing = expected_headers - actual_headers
        raise TSVLoadError(
            f"Fehlende Spalten in episodes.tsv: {', '.join(sorted(missing))}"
        )
    
    logger.info(f"Episoden geladen: {len(data)} Einträge")
    return data


def load_polls(file_path: Path) -> List[Dict[str, str]]:
    """
    Lädt die polls.tsv Datei und validiert das Schema.
    
    Args:
        file_path: Pfad zur polls.tsv
        
    Returns:
        Liste von Poll-Dictionaries (kann leer sein)
        
    Raises:
        TSVLoadError: Wenn die Datei nicht geladen werden kann oder Header falsch sind
    """
    if not file_path.exists():
        raise TSVLoadError(f"Datei nicht gefunden: {file_path}")
    
    # Header prüfen ohne vollständiges Laden
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            if reader.fieldnames is None:
                raise TSVLoadError(f"Keine Header-Zeile gefunden in {file_path}")
            
            # Erwartete Header in der richtigen Reihenfolge
            expected_headers = [
                'poll_id', 'reddit_post_id', 'created_at', 'closes_at',
                'episode_a_id', 'episode_b_id', 'votes_a', 'votes_b', 'finalized_at'
            ]
            
            actual_headers = list(reader.fieldnames)
            
            if actual_headers != expected_headers:
                raise TSVLoadError(
                    f"Header-Schema in polls.tsv stimmt nicht überein.\n"
                    f"Erwartet: {expected_headers}\n"
                    f"Gefunden: {actual_headers}"
                )
            
            # Daten laden (kann leer sein)
            data = list(reader)
            logger.info(f"Polls geladen: {len(data)} Einträge")
            return data
            
    except csv.Error as e:
        raise TSVLoadError(f"Fehler beim Parsen der TSV-Datei {file_path}: {e}")
    except TSVLoadError:
        raise
    except Exception as e:
        raise TSVLoadError(f"Fehler beim Laden der Datei {file_path}: {e}")

"""
TSV Datei-Loader

Dieses Modul stellt Funktionen zum Laden und Parsen von TSV-Dateien bereit.
Episoden werden nicht mehr aus TSV geladen, sondern über die Dreimetadaten API.
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


# Funktion load_episodes wurde entfernt - Episoden werden nun über die
# Dreimetadaten API geladen (siehe bot.dreimetadaten_api.fetch_all_episodes)


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


def load_ratings(file_path: Path) -> List[Dict[str, str]]:
    """
    Lädt die ratings.tsv Datei und validiert das Schema.
    
    Args:
        file_path: Pfad zur ratings.tsv
        
    Returns:
        Liste von Rating-Dictionaries (kann leer sein)
        
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
            expected_headers = ['episode_id', 'utility', 'matches', 'calculated_at']
            
            actual_headers = list(reader.fieldnames)
            
            if actual_headers != expected_headers:
                raise TSVLoadError(
                    f"Header-Schema in ratings.tsv stimmt nicht überein.\n"
                    f"Erwartet: {expected_headers}\n"
                    f"Gefunden: {actual_headers}"
                )
            
            # Daten laden (kann leer sein)
            data = list(reader)
            logger.info(f"Ratings geladen: {len(data)} Einträge")
            return data
            
    except csv.Error as e:
        raise TSVLoadError(f"Fehler beim Parsen der TSV-Datei {file_path}: {e}")
    except TSVLoadError:
        raise
    except Exception as e:
        raise TSVLoadError(f"Fehler beim Laden der Datei {file_path}: {e}")

"""
TSV Repository

Dieses Modul stellt Funktionen zum Laden, Validieren und Schreiben von TSV-Dateien bereit.
Zentraler Ort für alle TSV-Dateioperationen (polls.tsv, ratings.tsv).
Episoden werden nicht mehr aus TSV geladen, sondern über die Dreimetadaten API.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone
from bot.logger import get_logger

logger = get_logger(__name__)


class TSVError(Exception):
    """Exception für TSV-Fehler (Laden oder Schreiben)"""
    pass


# Legacy alias für Abwärtskompatibilität
TSVLoadError = TSVError


def load_tsv(file_path: Path) -> List[Dict[str, str]]:
    """
    Lädt eine TSV-Datei und gibt eine Liste von Dictionaries zurück.
    
    Args:
        file_path: Pfad zur TSV-Datei
        
    Returns:
        Liste von Dictionaries, wobei jeder Key ein Spaltenname ist
        
    Raises:
        TSVError: Wenn die Datei nicht geladen werden kann
    """
    if not file_path.exists():
        raise TSVError(f"Datei nicht gefunden: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            # Prüfen, ob Header vorhanden ist
            if reader.fieldnames is None:
                raise TSVError(f"Keine Header-Zeile gefunden in {file_path}")
            
            data = list(reader)
            logger.debug(f"TSV-Datei geladen: {file_path} ({len(data)} Zeilen)")
            return data
            
    except csv.Error as e:
        raise TSVError(f"Fehler beim Parsen der TSV-Datei {file_path}: {e}")
    except Exception as e:
        raise TSVError(f"Fehler beim Laden der Datei {file_path}: {e}")


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
        TSVError: Wenn die Datei nicht geladen werden kann oder Header falsch sind
    """
    if not file_path.exists():
        raise TSVError(f"Datei nicht gefunden: {file_path}")
    
    # Header prüfen ohne vollständiges Laden
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            if reader.fieldnames is None:
                raise TSVError(f"Keine Header-Zeile gefunden in {file_path}")
            
            # Erwartete Header in der richtigen Reihenfolge
            expected_headers = [
                'poll_id', 'reddit_post_id', 'created_at', 'closes_at',
                'episode_a_id', 'episode_b_id', 'votes_a', 'votes_b', 'finalized_at'
            ]
            
            actual_headers = list(reader.fieldnames)
            
            if actual_headers != expected_headers:
                raise TSVError(
                    f"Header-Schema in polls.tsv stimmt nicht überein.\n"
                    f"Erwartet: {expected_headers}\n"
                    f"Gefunden: {actual_headers}"
                )
            
            # Daten laden (kann leer sein)
            data = list(reader)
            logger.info(f"Polls geladen: {len(data)} Einträge")
            return data
            
    except csv.Error as e:
        raise TSVError(f"Fehler beim Parsen der TSV-Datei {file_path}: {e}")
    except TSVError:
        raise
    except Exception as e:
        raise TSVError(f"Fehler beim Laden der Datei {file_path}: {e}")


def load_ratings(file_path: Path) -> List[Dict[str, str]]:
    """
    Lädt die ratings.tsv Datei und validiert das Schema.
    
    Args:
        file_path: Pfad zur ratings.tsv
        
    Returns:
        Liste von Rating-Dictionaries (kann leer sein)
        
    Raises:
        TSVError: Wenn die Datei nicht geladen werden kann oder Header falsch sind
    """
    if not file_path.exists():
        raise TSVError(f"Datei nicht gefunden: {file_path}")
    
    # Header prüfen ohne vollständiges Laden
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            if reader.fieldnames is None:
                raise TSVError(f"Keine Header-Zeile gefunden in {file_path}")
            
            # Erwartete Header in der richtigen Reihenfolge
            expected_headers = ['episode_id', 'utility', 'matches', 'calculated_at']
            
            actual_headers = list(reader.fieldnames)
            
            if actual_headers != expected_headers:
                raise TSVError(
                    f"Header-Schema in ratings.tsv stimmt nicht überein.\n"
                    f"Erwartet: {expected_headers}\n"
                    f"Gefunden: {actual_headers}"
                )
            
            # Daten laden (kann leer sein)
            data = list(reader)
            logger.info(f"Ratings geladen: {len(data)} Einträge")
            return data
            
    except csv.Error as e:
        raise TSVError(f"Fehler beim Parsen der TSV-Datei {file_path}: {e}")
    except TSVError:
        raise
    except Exception as e:
        raise TSVError(f"Fehler beim Laden der Datei {file_path}: {e}")


def append_ratings(
    file_path: Path,
    ratings: List[Dict[str, Any]]
) -> None:
    """
    Hängt Rating-Zeilen an ratings.tsv an (append-only).
    
    Behandelt Header-Validierung explizit:
    - Datei existiert nicht → Header + Daten schreiben
    - Datei existiert, aber ist leer → Header + Daten schreiben
    - Datei existiert mit Header:
      - Header stimmt → nur Daten anhängen
      - Header stimmt nicht → Exception werfen
    
    Die Funktion übernimmt die Formatierung:
    - utility (float) → "%.6f" Format
    - calculated_at (datetime) → ISO-8601 UTC Format (YYYY-MM-DDTHH:MM:SSZ)
    
    Args:
        file_path: Pfad zu ratings.tsv
        ratings: Liste von Dictionaries mit Keys:
            - episode_id (int)
            - utility (float)
            - matches (int)
            - calculated_at (datetime)
        
    Raises:
        TSVError: Bei Schreibfehlern oder falschen Headern
    """
    if not ratings:
        logger.warning("Keine Ratings zum Schreiben vorhanden")
        return
    
    # Erwartete Header
    expected_headers = ['episode_id', 'utility', 'matches', 'calculated_at']
    
    # Prüfe ob Datei existiert und ob sie leer ist
    file_exists = file_path.exists()
    file_empty = False
    
    if file_exists:
        # Prüfe ob Datei leer ist
        try:
            file_size = file_path.stat().st_size
            file_empty = (file_size == 0)
        except Exception as e:
            raise TSVError(f"Fehler beim Prüfen der Dateigröße von {file_path}: {e}")
        
        # Wenn nicht leer, validiere Header
        if not file_empty:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f, delimiter='\t')
                    first_line = next(reader, None)
                    
                    if first_line is None:
                        # Datei existiert aber hat keinen Inhalt
                        file_empty = True
                    elif first_line != expected_headers:
                        raise TSVError(
                            f"Header-Schema in {file_path} stimmt nicht überein.\n"
                            f"Erwartet: {expected_headers}\n"
                            f"Gefunden: {first_line}\n"
                            f"Append-Operation abgebrochen."
                        )
            except TSVError:
                raise
            except Exception as e:
                raise TSVError(f"Fehler beim Lesen des Headers von {file_path}: {e}")
    
    # Schreibe Daten
    try:
        mode = 'a' if (file_exists and not file_empty) else 'w'
        
        with open(file_path, mode, encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            
            # Schreibe Header nur wenn Datei neu oder leer ist
            if not file_exists or file_empty:
                writer.writerow(expected_headers)
            
            # Schreibe Rating-Zeilen
            for rating in ratings:
                # Formatierung: Repository ist verantwortlich für Output-Format
                utility_str = f"{rating['utility']:.6f}"
                calculated_at = rating['calculated_at']
                
                # Validiere dass calculated_at ein UTC-aware datetime ist
                if not isinstance(calculated_at, datetime):
                    raise TSVError(
                        f"calculated_at muss ein datetime-Objekt sein, "
                        f"erhalten: {type(calculated_at).__name__}"
                    )
                
                if calculated_at.tzinfo is None or calculated_at.tzinfo.utcoffset(calculated_at) is None:
                    raise TSVError(
                        "calculated_at muss timezone-aware sein (UTC erforderlich). "
                        "Verwende datetime.now(timezone.utc) oder datetime.replace(tzinfo=timezone.utc)"
                    )
                
                # Formatiere als ISO-8601 UTC (YYYY-MM-DDTHH:MM:SSZ)
                timestamp_str = calculated_at.strftime('%Y-%m-%dT%H:%M:%SZ')
                
                writer.writerow([
                    rating['episode_id'],
                    utility_str,
                    rating['matches'],
                    timestamp_str
                ])
        
        logger.info(f"{len(ratings)} Rating-Zeilen geschrieben nach {file_path}")
        
    except Exception as e:
        raise TSVError(f"Fehler beim Schreiben nach {file_path}: {e}")

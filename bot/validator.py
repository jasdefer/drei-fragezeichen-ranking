"""
Validierungslogik für Daten

Dieses Modul enthält die Validierungslogik für Episoden (via API) und TSV-Dateien (Polls, Ratings).
"""

from typing import List, Dict, Set, Any
from bot.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Exception für Validierungsfehler"""
    pass


def validate_episodes(episodes: List[Dict[str, Any]]) -> None:
    """
    Validiert Episode-Daten von der Dreimetadaten API.
    
    Diese Funktion erwartet nur Episodennummern (von fetch_all_episodes()).
    
    Args:
        episodes: Liste von Episode-Dictionaries von der API (nur mit 'nummer' Feld)
        
    Raises:
        ValidationError: Wenn Validierungsfehler gefunden werden
    """
    errors = []
    seen_ids: Set[int] = set()
    
    for idx, episode in enumerate(episodes, start=1):
        nummer = episode.get('nummer')
        
        # Validierung: nummer muss vorhanden und eindeutig sein
        if nummer is None:
            errors.append(f"Episode {idx}: nummer darf nicht leer sein")
        elif not isinstance(nummer, int):
            errors.append(f"Episode {idx}: nummer muss eine Ganzzahl sein, ist aber {type(nummer)}")
        elif nummer in seen_ids:
            errors.append(f"Episode {idx}: nummer '{nummer}' ist nicht eindeutig")
        else:
            seen_ids.add(nummer)
    
    if errors:
        error_msg = "Validierungsfehler in API-Episoden gefunden:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ValidationError(error_msg)
    
    logger.info(f"Alle {len(episodes)} Episoden erfolgreich validiert")


def validate_polls_schema(polls: List[Dict[str, str]]) -> None:
    """
    Validiert das Schema der polls.tsv.
    
    Da die Datei leer sein kann, prüfen wir hauptsächlich,
    dass die Header korrekt sind (wird bereits im Loader gemacht).
    
    Args:
        polls: Liste von Poll-Dictionaries
    """
    # Basis-Validierung ist bereits im Loader erfolgt
    # Hier könnten weitere Checks hinzugefügt werden
    logger.info(f"Polls-Schema validiert ({len(polls)} Einträge)")


def validate_ratings(ratings: List[Dict[str, str]], episodes: List[Dict[str, Any]]) -> None:
    """
    Validiert Rating-Daten.
    
    Args:
        ratings: Liste von Rating-Dictionaries
        episodes: Liste von Episode-Dictionaries für Referenzvalidierung (von der API)
        
    Raises:
        ValidationError: Wenn Validierungsfehler gefunden werden
    """
    errors = []
    
    # Erstelle Set aller gültigen episode-Nummern
    valid_episode_ids = {episode['nummer'] for episode in episodes}
    
    for idx, rating in enumerate(ratings, start=2):  # Start bei 2 (Header ist Zeile 1)
        episode_id = rating.get('episode_id', '').strip()
        utility = rating.get('utility', '').strip()
        matches = rating.get('matches', '').strip()
        calculated_at = rating.get('calculated_at', '').strip()
        
        # Validierung: episode_id muss vorhanden sein
        if not episode_id:
            errors.append(f"Zeile {idx}: episode_id darf nicht leer sein")
        else:
            try:
                episode_id_int = int(episode_id)
                if episode_id_int not in valid_episode_ids:
                    errors.append(
                        f"Zeile {idx}: episode_id '{episode_id}' existiert nicht in der API"
                    )
            except ValueError:
                errors.append(
                    f"Zeile {idx}: episode_id '{episode_id}' ist keine gültige Ganzzahl"
                )
        
        # Validierung: utility muss eine gültige Zahl sein
        if utility:
            try:
                float(utility)
            except ValueError:
                errors.append(
                    f"Zeile {idx} (ID: {episode_id}): "
                    f"utility '{utility}' ist keine gültige Gleitkommazahl"
                )
        else:
            errors.append(f"Zeile {idx} (ID: {episode_id}): utility darf nicht leer sein")
        
        # Validierung: matches muss eine nicht-negative Ganzzahl sein
        if matches:
            try:
                matches_int = int(matches)
                if matches_int < 0:
                    errors.append(
                        f"Zeile {idx} (ID: {episode_id}): "
                        f"matches '{matches}' darf nicht negativ sein"
                    )
            except ValueError:
                errors.append(
                    f"Zeile {idx} (ID: {episode_id}): "
                    f"matches '{matches}' ist keine gültige Ganzzahl"
                )
        else:
            errors.append(f"Zeile {idx} (ID: {episode_id}): matches darf nicht leer sein")
        
        # Validierung: calculated_at muss vorhanden sein und ISO 8601 Format haben
        if not calculated_at:
            errors.append(f"Zeile {idx} (ID: {episode_id}): calculated_at darf nicht leer sein")
        else:
            # Prüfe ISO 8601 Format (grundlegende Validierung)
            # Erwartetes Format: YYYY-MM-DDTHH:MM:SSZ
            import re
            iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
            if not re.match(iso8601_pattern, calculated_at):
                errors.append(
                    f"Zeile {idx} (ID: {episode_id}): "
                    f"calculated_at '{calculated_at}' entspricht nicht dem ISO 8601 Format "
                    f"(erwartet: YYYY-MM-DDTHH:MM:SSZ)"
                )
    
    if errors:
        error_msg = "Validierungsfehler in ratings.tsv gefunden:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ValidationError(error_msg)
    
    logger.info(f"Alle {len(ratings)} Ratings erfolgreich validiert")

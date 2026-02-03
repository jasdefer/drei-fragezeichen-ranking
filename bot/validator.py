"""
Validierungslogik für TSV-Dateien

Dieses Modul enthält die Validierungslogik für Episoden und Umfragen.
"""

from typing import List, Dict, Set
from bot.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Exception für Validierungsfehler"""
    pass


# Erlaubte Werte für das 'type' Feld
ALLOWED_EPISODE_TYPES = {'regular', 'special'}


def validate_episodes(episodes: List[Dict[str, str]]) -> None:
    """
    Validiert Episode-Daten.
    
    Args:
        episodes: Liste von Episode-Dictionaries
        
    Raises:
        ValidationError: Wenn Validierungsfehler gefunden werden
    """
    errors = []
    seen_ids: Set[str] = set()
    
    for idx, episode in enumerate(episodes, start=2):  # Start bei 2 (Header ist Zeile 1)
        episode_id = episode.get('episode_id', '').strip()
        title = episode.get('title', '').strip()
        year = episode.get('year', '').strip()
        episode_type = episode.get('type', '').strip()
        
        # Validierung: episode_id muss vorhanden und eindeutig sein
        if not episode_id:
            errors.append(f"Zeile {idx}: episode_id darf nicht leer sein")
        elif episode_id in seen_ids:
            errors.append(f"Zeile {idx}: episode_id '{episode_id}' ist nicht eindeutig")
        else:
            seen_ids.add(episode_id)
        
        # Validierung: title darf nicht leer sein
        if not title:
            errors.append(f"Zeile {idx} (ID: {episode_id}): title darf nicht leer sein")
        
        # Validierung: year ist optional, aber falls gesetzt muss es eine gültige Jahreszahl sein
        if year:
            try:
                year_int = int(year)
                if year_int < 1900 or year_int > 2100:
                    errors.append(
                        f"Zeile {idx} (ID: {episode_id}): "
                        f"year '{year}' liegt außerhalb des plausiblen Bereichs (1900-2100)"
                    )
            except ValueError:
                errors.append(
                    f"Zeile {idx} (ID: {episode_id}): "
                    f"year '{year}' ist keine gültige Ganzzahl"
                )
        
        # Validierung: type muss aus erlaubter Menge stammen
        if not episode_type:
            errors.append(f"Zeile {idx} (ID: {episode_id}): type darf nicht leer sein")
        elif episode_type not in ALLOWED_EPISODE_TYPES:
            errors.append(
                f"Zeile {idx} (ID: {episode_id}): "
                f"type '{episode_type}' ist nicht erlaubt. "
                f"Erlaubte Werte: {', '.join(sorted(ALLOWED_EPISODE_TYPES))}"
            )
    
    if errors:
        error_msg = "Validierungsfehler in episodes.tsv gefunden:\n" + "\n".join(errors)
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


def validate_ratings(ratings: List[Dict[str, str]], episodes: List[Dict[str, str]]) -> None:
    """
    Validiert Rating-Daten.
    
    Args:
        ratings: Liste von Rating-Dictionaries
        episodes: Liste von Episode-Dictionaries für Referenzvalidierung
        
    Raises:
        ValidationError: Wenn Validierungsfehler gefunden werden
    """
    errors = []
    
    # Erstelle Set aller gültigen episode_ids
    valid_episode_ids = {episode['episode_id'] for episode in episodes}
    
    for idx, rating in enumerate(ratings, start=2):  # Start bei 2 (Header ist Zeile 1)
        episode_id = rating.get('episode_id', '').strip()
        utility = rating.get('utility', '').strip()
        matches = rating.get('matches', '').strip()
        calculated_at = rating.get('calculated_at', '').strip()
        
        # Validierung: episode_id muss vorhanden sein
        if not episode_id:
            errors.append(f"Zeile {idx}: episode_id darf nicht leer sein")
        elif episode_id not in valid_episode_ids:
            errors.append(
                f"Zeile {idx}: episode_id '{episode_id}' existiert nicht in episodes.tsv"
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

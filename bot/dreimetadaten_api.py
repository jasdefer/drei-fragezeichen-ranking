"""
Dreimetadaten API Wrapper

Dieses Modul stellt einen generischen API-Wrapper für die Dreimetadaten SQL-API bereit
mit Logging, Fehlerhandling und expliziten Helper-Funktionen.

API-Endpoint: https://api.dreimetadaten.de/db.json
"""

import requests
import time
from typing import Dict, List, Union, Optional, Any
from bot.logger import get_logger

logger = get_logger(__name__)


class APIError(Exception):
    """Exception für API-bezogene Fehler"""
    pass


class APITimeoutError(APIError):
    """Exception für Timeout-Fehler"""
    pass


class APIResponseError(APIError):
    """Exception für fehlerhafte API-Antworten"""
    pass


def run_query(
    query: str,
    timeout: int = 30,
    max_retries: int = 3
) -> Union[Dict, List]:
    """
    Führt einen SQL-Query gegen die Dreimetadaten API aus.
    
    Args:
        query: SQL-Query-String (ohne URL-Encoding)
        timeout: Request-Timeout in Sekunden (Standard: 30)
        max_retries: Maximale Anzahl von Wiederholungsversuchen bei Fehlern (Standard: 3)
        
    Returns:
        JSON-Antwort als Dictionary oder Liste
        
    Raises:
        APIError: Bei allgemeinen API-Fehlern
        APITimeoutError: Bei Timeout-Fehlern
        APIResponseError: Bei fehlerhaften API-Antworten (z.B. ungültiges JSON)
        
    Example:
        >>> query = "SELECT * FROM serie LIMIT 5"
        >>> result = run_query(query)
    """
    base_url = "https://api.dreimetadaten.de/db.json"
    
    # Parameter für die API
    params = {
        'sql': query,
        '_shape': 'array'  # Gibt Ergebnis als JSON-Array zurück
    }

    prepared_request = requests.Request("GET", base_url, params=params).prepare()
    request_url = prepared_request.url or base_url
    query_compact = " ".join(query.split())
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            logger.debug(
                f"API-Request (Versuch {attempt + 1}/{max_retries}): {query[:100]}..."
            )
            logger.debug(
                "API-Request-Details: url_len=%s, query_len=%s, timeout=%ss",
                len(request_url),
                len(query_compact),
                timeout,
            )
            
            response = requests.get(
                base_url,
                params=params,
                timeout=timeout
            )
            
            # Prüfe HTTP-Statuscode
            if response.status_code != 200:
                error_msg = (
                    f"API-Fehler: HTTP {response.status_code} - {response.reason}"
                )
                logger.warning(
                    "%s | content-length=%s, transfer-encoding=%s, content-encoding=%s",
                    error_msg,
                    response.headers.get("content-length"),
                    response.headers.get("transfer-encoding"),
                    response.headers.get("content-encoding"),
                )
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponentielles Backoff
                    logger.info(f"Warte {wait_time}s vor erneutem Versuch...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise APIResponseError(error_msg)
            
            # Versuche JSON zu parsen
            try:
                data = response.json()
                logger.debug(f"API-Request erfolgreich, {len(data) if isinstance(data, list) else 1} Ergebnisse")
                return data
                
            except ValueError as e:
                error_msg = f"API-Antwort ist kein gültiges JSON: {e}"
                logger.error(
                    "%s | status=%s, content-length=%s, body-prefix=%r",
                    error_msg,
                    response.status_code,
                    response.headers.get("content-length"),
                    response.text[:240],
                )
                raise APIResponseError(error_msg)
        
        except requests.Timeout as e:
            error_msg = f"Timeout beim API-Request nach {timeout}s"
            logger.warning("%s | type=%s, detail=%r", error_msg, type(e).__name__, e)
            last_error = APITimeoutError(error_msg)
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Warte {wait_time}s vor erneutem Versuch...")
                time.sleep(wait_time)
            else:
                raise last_error
        
        except requests.RequestException as e:
            error_msg = f"Fehler beim API-Request: {e}"
            response = getattr(e, "response", None)
            status = response.status_code if response is not None else None
            headers = response.headers if response is not None else None
            logger.warning(
                "%s | type=%s, detail=%r, url_len=%s, status=%s, content-length=%s, transfer-encoding=%s",
                error_msg,
                type(e).__name__,
                e,
                len(request_url),
                status,
                headers.get("content-length") if headers else None,
                headers.get("transfer-encoding") if headers else None,
            )
            if e.__cause__ is not None:
                logger.debug("API-Request-Exception-Cause: %r", e.__cause__)
            last_error = APIError(error_msg)
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Warte {wait_time}s vor erneutem Versuch...")
                time.sleep(wait_time)
            else:
                raise last_error
    
    # Sollte nie erreicht werden, aber als Fallback
    if last_error:
        raise last_error
    raise APIError("Unbekannter Fehler beim API-Request")


def fetch_all_episodes() -> List[Dict[str, Any]]:
    """
    Lädt nur die Nummern aller Episoden von der Dreimetadaten API.
    
    Für detaillierte Metadaten einzelner Episoden verwende fetch_episode_metadata().
    
    Returns:
        Liste von Episode-Dictionaries mit dem Feld:
        - nummer (int): Folgennummer
        
    Raises:
        APIError: Bei Fehlern während des API-Aufrufs
        
    Example:
        >>> episodes = fetch_all_episodes()
        >>> print(f"Gefunden: {len(episodes)} Episoden")
        >>> # Für Metadaten einer Episode:
        >>> metadata = fetch_episode_metadata(episodes[0]['nummer'])
    """
    query = """
    SELECT 
        s.nummer
    FROM serie s
    ORDER BY s.nummer
    """
    
    logger.info("Lade alle Episoden von der API...")
    
    try:
        episodes = run_query(query)
        
        if not isinstance(episodes, list):
            raise APIResponseError(
                f"Erwartete Liste von Episoden, erhielt {type(episodes)}"
            )
        
        logger.info(f"Erfolgreich {len(episodes)} Episoden geladen")
        return episodes
        
    except APIError as e:
        logger.error(f"Fehler beim Laden der Episoden: {e}")
        raise


def fetch_all_episode_metadata() -> List[Dict[str, Any]]:
    """
    Laedt Metadaten fuer alle Episoden von der Dreimetadaten API.

    Returns:
        Liste von Episode-Dictionaries mit den Feldern:
        - nummer (int): Folgennummer
        - titel (str): Titel der Folge
        - kurzbeschreibung (str): Kurzbeschreibung der Folge (optional)
        - urlCoverApple (str): URL zum Cover-Bild

    Raises:
        APIError: Bei Fehlern waehrend des API-Aufrufs
        APIResponseError: Wenn die API-Antwort nicht das erwartete Format hat
    """
    query = """
    SELECT
        s.nummer,
        h.titel,
        h.kurzbeschreibung,
        h.urlCoverApple
    FROM serie s
    JOIN hörspiel h ON h.hörspielID = s.hörspielID
    ORDER BY s.nummer
    """

    logger.info("Lade Metadaten fuer alle Episoden von der API...")

    try:
        episodes = run_query(query)

        if not isinstance(episodes, list):
            raise APIResponseError(
                f"Erwartete Liste von Episoden-Metadaten, erhielt {type(episodes)}"
            )

        logger.info("Erfolgreich %s Episoden-Metadaten geladen", len(episodes))
        return episodes

    except APIError as e:
        logger.error("Fehler beim Laden der Episoden-Metadaten: %s", e)
        raise


def fetch_episode_metadata(nummer: int) -> Optional[Dict[str, Any]]:
    """
    Lädt Metadaten einer spezifischen Episode von der Dreimetadaten API.
    
    Args:
        nummer: Folgennummer der gewünschten Episode
        
    Returns:
        Dictionary mit Episode-Metadaten oder None falls nicht gefunden:
        - nummer (int): Folgennummer
        - titel (str): Titel der Folge
        - beschreibung (str): Beschreibung der Folge
        - urlCoverApple (str): URL zum Cover-Bild
        
    Raises:
        APIError: Bei Fehlern während des API-Aufrufs
        ValueError: Wenn nummer keine gültige Ganzzahl ist
        
    Example:
        >>> episode = fetch_episode_metadata(149)
        >>> if episode:
        ...     print(episode['titel'])
    """
    # Validiere nummer als Integer zur Vermeidung von SQL-Injection
    if not isinstance(nummer, int):
        raise ValueError(f"nummer muss eine Ganzzahl sein, ist aber {type(nummer)}")
    
    query = f"""
    SELECT 
        s.nummer,
        h.titel,
        h.beschreibung,
        h.urlCoverApple
    FROM serie s
    JOIN hörspiel h ON h.hörspielID = s.hörspielID
    WHERE s.nummer = {nummer}
    """
    
    logger.info(f"Lade Metadaten für Episode {nummer}...")
    
    try:
        result = run_query(query)
        
        if not isinstance(result, list):
            raise APIResponseError(
                f"Erwartete Liste, erhielt {type(result)}"
            )
        
        if len(result) == 0:
            logger.warning(f"Episode {nummer} nicht gefunden")
            return None
        
        if len(result) > 1:
            logger.warning(
                f"Mehrere Ergebnisse für Episode {nummer} gefunden, "
                f"verwende das erste"
            )
        
        episode = result[0]
        logger.debug(f"Episode {nummer} geladen: {episode.get('titel', 'N/A')}")
        return episode
        
    except APIError as e:
        logger.error(f"Fehler beim Laden der Episode {nummer}: {e}")
        raise

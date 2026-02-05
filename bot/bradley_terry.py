"""
Bradley-Terry Modell für Episode-Rankings

Dieses Modul implementiert das Bradley-Terry-Modell zur Berechnung von 
Episode-Rankings basierend auf paarweisen Vergleichsdaten aus polls.tsv.

Methodik:
- Bradley-Terry Discrete Choice Model
- MM-Algorithmus (Minorization-Maximization)
- L2-Regularisierung (alpha = 0.01)
- Nur Episoden berücksichtigt, die mit Episode 1 verbunden sind
- Normierung: mean(utility) = 1.0

Hinweis: Votes werden zu Einzelbeobachtungen expandiert (disaggregiert).
Dies ist mathematisch äquivalent zur Binomial-Likelihood, aber weniger effizient.

Siehe auch: docs/bradley_terry_research.md
"""

from pathlib import Path
from typing import List, Dict, Tuple, Set
from datetime import datetime, timezone
from collections import defaultdict, deque

import choix
import numpy as np

from bot.logger import get_logger
from bot.tsv_repository import load_polls, append_ratings, TSVError

logger = get_logger(__name__)


class BradleyTerryError(Exception):
    """Exception für Bradley-Terry-Berechnungsfehler"""
    pass


def parse_datetime_utc(datetime_str: str) -> datetime:
    """
    Parst einen ISO-8601 Timestamp und gibt ein UTC datetime zurück.
    
    Args:
        datetime_str: ISO-8601 formatierter Timestamp
        
    Returns:
        datetime-Objekt in UTC
        
    Raises:
        BradleyTerryError: Wenn das Datum nicht geparst werden kann
    """
    if not datetime_str:
        raise BradleyTerryError(f"Leerer Timestamp: '{datetime_str}'")
    
    try:
        # Parse ISO format
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        # Ensure UTC timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except (ValueError, AttributeError) as e:
        raise BradleyTerryError(f"Ungültiges Zeitformat: '{datetime_str}' - {e}")


def filter_and_parse_polls(raw_polls: List[Dict[str, str]], calculated_at: datetime) -> List[Dict]:
    """
    Filtert und parst Poll-Daten.
    
    Nur Polls mit finalized_at <= calculated_at werden berücksichtigt.
    Polls mit votes_a + votes_b == 0 werden geloggt und ignoriert.
    
    Args:
        raw_polls: Rohe Poll-Daten von tsv_repository.load_polls()
        calculated_at: Cutoff-Zeit für finalisierte Polls (UTC)
        
    Returns:
        Liste von Poll-Dictionaries mit parseten Integer-Werten
        
    Raises:
        BradleyTerryError: Bei Parse-Fehlern oder Validierungsfehlern
    """
    finalized_polls = []
    zero_vote_count = 0
    
    logger.info(f"Polls geladen: {len(raw_polls)} Einträge")
    
    for poll in raw_polls:
        # Prüfe ob finalized_at gesetzt ist
        if not poll.get('finalized_at'):
            continue
        
        # Parse finalized_at
        try:
            finalized_at = parse_datetime_utc(poll['finalized_at'])
        except BradleyTerryError as e:
            raise BradleyTerryError(
                f"Fehler beim Parsen von finalized_at in Poll "
                f"{poll.get('poll_id', 'unknown')}: {e}"
            )
        
        # Nur Polls bis calculated_at verwenden
        if finalized_at > calculated_at:
            continue
        
        # Parse IDs und Votes
        try:
            episode_a_id = int(poll['episode_a_id'])
            episode_b_id = int(poll['episode_b_id'])
            votes_a = int(poll['votes_a'])
            votes_b = int(poll['votes_b'])
        except (ValueError, KeyError) as e:
            raise BradleyTerryError(
                f"Fehler beim Parsen von Poll {poll.get('poll_id', 'unknown')}: {e}"
            )
        
        # Validierung: episode_a_id != episode_b_id
        if episode_a_id == episode_b_id:
            raise BradleyTerryError(
                f"Poll {poll.get('poll_id', 'unknown')}: "
                f"episode_a_id und episode_b_id sind identisch ({episode_a_id})"
            )
        
        # Validierung: votes >= 0
        if votes_a < 0 or votes_b < 0:
            raise BradleyTerryError(
                f"Poll {poll.get('poll_id', 'unknown')}: "
                f"Negative Stimmen nicht erlaubt (votes_a={votes_a}, votes_b={votes_b})"
            )
        
        # Prüfe auf 0 Votes
        if votes_a + votes_b == 0:
            zero_vote_count += 1
            logger.warning(
                f"Poll {poll.get('poll_id', 'unknown')} hat 0 Stimmen "
                f"(Episode {episode_a_id} vs {episode_b_id}) - wird ignoriert"
            )
            continue
        
        # Poll aufbereitet hinzufügen
        finalized_polls.append({
            'poll_id': poll.get('poll_id', 'unknown'),
            'episode_a_id': episode_a_id,
            'episode_b_id': episode_b_id,
            'votes_a': votes_a,
            'votes_b': votes_b,
            'finalized_at': finalized_at
        })
    
    logger.info(f"Finalisierte Polls: {len(finalized_polls)}")
    if zero_vote_count > 0:
        logger.info(f"Polls mit 0 Stimmen ignoriert: {zero_vote_count}")
    
    return finalized_polls



def build_connectivity_graph(polls: List[Dict]) -> Dict[int, Set[int]]:
    """
    Erstellt einen ungerichteten Graph der Episode-Vergleiche.
    
    Args:
        polls: Liste von Poll-Dictionaries mit episode_a_id und episode_b_id
        
    Returns:
        Adjazenzliste als Dict[episode_id, Set[episode_id]]
    """
    graph = defaultdict(set)
    
    for poll in polls:
        a = poll['episode_a_id']
        b = poll['episode_b_id']
        graph[a].add(b)
        graph[b].add(a)
    
    return dict(graph)


def find_connected_component(graph: Dict[int, Set[int]], start_node: int) -> Set[int]:
    """
    Findet die Zusammenhangskomponente, die start_node enthält.
    
    Verwendet BFS (Breadth-First Search) mit deque für bessere Performance.
    
    Args:
        graph: Adjazenzliste
        start_node: Startknoten (Episode-ID)
        
    Returns:
        Set von Episode-IDs in der Zusammenhangskomponente
    """
    if start_node not in graph:
        return set()
    
    visited = set()
    queue = deque([start_node])
    
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        
        visited.add(node)
        
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                queue.append(neighbor)
    
    return visited


def filter_polls_by_episodes(polls: List[Dict], valid_episodes: Set[int]) -> List[Dict]:
    """
    Filtert Polls, sodass nur solche mit Episoden aus valid_episodes bleiben.
    
    Args:
        polls: Liste von Poll-Dictionaries
        valid_episodes: Set von gültigen Episode-IDs
        
    Returns:
        Gefilterte Liste von Polls
    """
    filtered = []
    for poll in polls:
        if (poll['episode_a_id'] in valid_episodes and 
            poll['episode_b_id'] in valid_episodes):
            filtered.append(poll)
    return filtered


def prepare_pairwise_data_expanded(polls: List[Dict], episode_ids: List[int]) -> List[Tuple[int, int]]:
    """
    Bereitet Paarvergleichsdaten für choix auf (Disaggregierung zu Einzelbeobachtungen).
    
    Jeder Poll mit votes_a und votes_b wird zu votes_a + votes_b Einzelbeobachtungen
    expandiert. Dies ist mathematisch äquivalent zur Binomial-Likelihood, aber
    weniger effizient als eine direkte Binomial-Formulierung.
    
    Args:
        polls: Liste von Poll-Dictionaries
        episode_ids: Sortierte Liste von Episode-IDs (für Index-Mapping)
        
    Returns:
        Liste von (winner_idx, loser_idx) Tupeln (expandiert nach Vote-Counts)
    """
    # Mapping: episode_id -> index
    id_to_idx = {ep_id: idx for idx, ep_id in enumerate(episode_ids)}
    
    # Liste für expandierte Vergleiche
    comparisons = []
    
    for poll in polls:
        idx_a = id_to_idx[poll['episode_a_id']]
        idx_b = id_to_idx[poll['episode_b_id']]
        votes_a = poll['votes_a']
        votes_b = poll['votes_b']
        
        # Expandiere votes_a mal: A schlägt B
        for _ in range(votes_a):
            comparisons.append((idx_a, idx_b))
        
        # Expandiere votes_b mal: B schlägt A
        for _ in range(votes_b):
            comparisons.append((idx_b, idx_a))
    
    return comparisons


def count_matches_per_episode(polls: List[Dict], episode_ids: List[int]) -> Dict[int, int]:
    """
    Zählt die Anzahl der Matches pro Episode.
    
    Args:
        polls: Liste von Poll-Dictionaries
        episode_ids: Liste von Episode-IDs
        
    Returns:
        Dict[episode_id, match_count]
    """
    match_counts = {ep_id: 0 for ep_id in episode_ids}
    
    for poll in polls:
        match_counts[poll['episode_a_id']] += 1
        match_counts[poll['episode_b_id']] += 1
    
    return match_counts


def fit_bradley_terry_model(
    data: List[Tuple[int, int]],
    n_items: int,
    alpha: float = 0.01,
    max_iter: int = 10000,
    tol: float = 1e-6
) -> np.ndarray:
    """
    Fittet das Bradley-Terry-Modell mit MM-Algorithmus.
    
    Args:
        data: Pairwise comparison data als Liste von (winner_idx, loser_idx)
        n_items: Anzahl der Items (Episoden)
        alpha: L2-Regularisierungsstärke
        max_iter: Maximale Iterationen
        tol: Konvergenztoleranz
        
    Returns:
        Log-Stärken theta (n_items,)
        
    Raises:
        BradleyTerryError: Bei Konvergenzfehlern oder numerischen Problemen
    """
    try:
        # Fit Bradley-Terry mit MM-Algorithmus
        theta = choix.mm_pairwise(
            n_items=n_items,
            data=data,
            alpha=alpha,
            max_iter=max_iter,
            tol=tol
        )
        
        # Post-Fit Sanity Check: Prüfe auf numerische Probleme
        if not np.isfinite(theta).all():
            raise BradleyTerryError(
                f"Modell-Fit hat nicht-finite Werte produziert: "
                f"NaN-Count: {np.isnan(theta).sum()}, "
                f"Inf-Count: {np.isinf(theta).sum()}"
            )
        
        return theta
        
    except Exception as e:
        if isinstance(e, BradleyTerryError):
            raise
        raise BradleyTerryError(f"Fehler beim Fitten des Bradley-Terry-Modells: {e}")


def normalize_utilities(theta: np.ndarray) -> np.ndarray:
    """
    Konvertiert log-Stärken zu normalisierten Utilities.
    
    Schritte:
    1. pi = exp(theta)
    2. utility = pi / mean(pi)  # Arithmetisches Mittel = 1.0
    
    Args:
        theta: Log-Stärken (choix gibt geometric_mean = 1)
        
    Returns:
        Normierte Utilities mit mean = 1.0
    """
    pi = np.exp(theta)
    mean_pi = np.mean(pi)
    utilities = pi / mean_pi
    return utilities


def compute_ratings_from_polls(
    polls: List[Dict],
    calculated_at: datetime
) -> List[Dict]:
    """
    Berechnet Bradley-Terry Ratings aus Polls - REIN, ohne I/O.
    
    Diese Funktion ist vollständig I/O-frei und daher ideal für Tests.
    Sie nimmt Polls entgegen und gibt Rating-Daten zurück.
    
    Ablauf:
    1. Baue Konnektivitätsgraph
    2. Finde Komponente mit Episode 1
    3. Filtere Polls und Episoden
    4. Bereite Daten für choix vor
    5. Fitte Bradley-Terry-Modell
    6. Berechne normierte Utilities
    7. Gebe Rating-Rows zurück
    
    Args:
        polls: Bereits geparste Poll-Daten (mit episode_a_id, episode_b_id, votes_a, votes_b)
        calculated_at: UTC-Zeitpunkt der Berechnung (muss timezone-aware UTC sein)
        
    Returns:
        Liste von Rating-Dictionaries mit Feldern:
        - episode_id: int
        - utility: float (normiert, mean = 1.0)
        - matches: int (Anzahl Vergleiche)
        - calculated_at: datetime (timezone-aware UTC)
        
    Raises:
        BradleyTerryError: Bei allen kritischen Fehlern
    """
    # Validiere dass calculated_at timezone-aware UTC ist
    if calculated_at.tzinfo is None:
        raise BradleyTerryError(
            "calculated_at muss ein timezone-aware datetime sein. "
            "Verwenden Sie datetime.now(timezone.utc)."
        )
    
    # Prüfe dass es UTC ist (Offset muss 0 sein)
    from datetime import timedelta
    if calculated_at.utcoffset() != timedelta(0):
        raise BradleyTerryError(
            "calculated_at muss UTC timezone verwenden (UTC offset = 0). "
            f"Aktuell: {calculated_at.tzinfo} mit offset {calculated_at.utcoffset()}. "
            "Verwenden Sie datetime.now(timezone.utc)."
        )
    
    if not polls:
        logger.warning("Keine Polls zum Verarbeiten - leere Berechnung")
        return []
    
    # 1. Baue Graph
    logger.info("Baue Konnektivitätsgraph...")
    graph = build_connectivity_graph(polls)
    logger.info(f"Graph enthält {len(graph)} Episoden")
    
    # 2. Finde Komponente mit Episode 1
    if 1 not in graph:
        raise BradleyTerryError(
            "Episode 1 ist nicht im Vergleichsgraph vorhanden. "
            "Modell kann nicht sinnvoll berechnet werden."
        )
    
    connected_episodes = find_connected_component(graph, start_node=1)
    logger.info(f"Episoden verbunden mit Episode 1: {len(connected_episodes)}")
    
    # Logge gedroppte Episoden
    all_episodes = set(graph.keys())
    dropped_episodes = all_episodes - connected_episodes
    if dropped_episodes:
        logger.warning(
            f"{len(dropped_episodes)} Episoden NICHT mit Episode 1 verbunden "
            f"und werden ignoriert: {sorted(dropped_episodes)}"
        )
    
    # 3. Filtere Polls
    filtered_polls = filter_polls_by_episodes(polls, connected_episodes)
    logger.info(f"Polls nach Filterung: {len(filtered_polls)}")
    
    # Edge-Case: Episode 1 im Graph, aber keine Polls nach Filterung
    if not filtered_polls:
        raise BradleyTerryError(
            "Episode 1 ist im Vergleichsgraph, aber keine Polls nach "
            "Connectivity-Filterung übrig. Dies deutet auf ein Datenproblem hin."
        )
    
    # 4. Sortiere Episode-IDs für konsistente Indizierung
    episode_ids = sorted(list(connected_episodes))
    logger.info(f"Episoden im Modell: {len(episode_ids)}")
    
    # 5. Bereite Daten vor (Disaggregierung zu Einzelbeobachtungen)
    pairwise_data = prepare_pairwise_data_expanded(filtered_polls, episode_ids)
    logger.info(f"Pairwise comparisons: {len(pairwise_data)}")
    
    # 6. Zähle Matches
    match_counts = count_matches_per_episode(filtered_polls, episode_ids)
    
    # 7. Fitte Modell
    logger.info("Fitte Bradley-Terry-Modell (MM, alpha=0.01)...")
    theta = fit_bradley_terry_model(
        data=pairwise_data,
        n_items=len(episode_ids),
        alpha=0.01
    )
    logger.info(f"Modell konvergiert, theta shape: {theta.shape}")
    
    # 8. Normiere Utilities
    utilities = normalize_utilities(theta)
    logger.info(f"Utilities berechnet - mean: {np.mean(utilities):.6f}, std: {np.std(utilities):.6f}")
    
    # 9. Bereite Rating-Rows vor und gebe zurück
    rating_rows = []
    for ep_id, utility in zip(episode_ids, utilities):
        rating_rows.append({
            'episode_id': ep_id,
            'utility': utility,  # float
            'matches': match_counts[ep_id],
            'calculated_at': calculated_at  # datetime (timezone-aware UTC)
        })
    
    # Finale Metriken
    logger.info(f"=== Berechnung abgeschlossen ===")
    logger.info(f"Verwendete Polls: {len(filtered_polls)}")
    logger.info(f"Gerankte Episoden: {len(episode_ids)}")
    logger.info(f"Gedroppte Episoden: {len(dropped_episodes)}")
    
    return rating_rows


def run_rating_update_from_polls(
    polls: List[Dict],
    ratings_path: Path,
    calculated_at: datetime
) -> None:
    """
    Führt Bradley-Terry Rating-Update durch und schreibt zu ratings.tsv.
    
    Wrapper um compute_ratings_from_polls(), der das Ergebnis
    über tsv_repository in die Datei schreibt.
    
    Args:
        polls: Bereits geparste Poll-Daten (mit episode_a_id, episode_b_id, votes_a, votes_b)
        ratings_path: Pfad zu ratings.tsv
        calculated_at: UTC-Zeitpunkt der Berechnung (muss timezone-aware UTC sein)
        
    Raises:
        BradleyTerryError: Bei allen kritischen Fehlern
        TSVError: Bei Problemen beim Schreiben von ratings.tsv
    """
    # Berechne Ratings (I/O-frei)
    rating_rows = compute_ratings_from_polls(polls, calculated_at)
    
    if not rating_rows:
        logger.warning("Keine Ratings berechnet - nichts zu schreiben")
        return
    
    # Schreibe zu ratings.tsv über tsv_repository
    try:
        append_ratings(ratings_path, rating_rows)
    except TSVError as e:
        raise BradleyTerryError(f"Fehler beim Schreiben von ratings.tsv: {e}")
    
    logger.info(f"=== Update in ratings.tsv geschrieben ===")


def run_rating_update(
    polls_path: Path,
    ratings_path: Path,
    calculated_at: datetime = None
) -> None:
    """
    Führt ein vollständiges Bradley-Terry Rating-Update durch.
    
    Lädt Polls aus polls.tsv, filtert und verarbeitet sie.
    Delegiert die eigentliche Berechnung an run_rating_update_from_polls().
    
    Args:
        polls_path: Pfad zu polls.tsv
        ratings_path: Pfad zu ratings.tsv
        calculated_at: Optional - UTC-Zeitpunkt der Berechnung (default: jetzt)
        
    Raises:
        BradleyTerryError: Bei allen kritischen Fehlern
        TSVError: Bei Problemen mit dem Dateiformat
    """
    # Bestimme calculated_at
    if calculated_at is None:
        calculated_at = datetime.now(timezone.utc)
    
    logger.info(f"=== Bradley-Terry Rating Update ===")
    logger.info(f"Calculated at: {calculated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # 1. Lade Polls über tsv_repository (validiert Schema)
    try:
        raw_polls = load_polls(polls_path)
    except TSVError as e:
        raise BradleyTerryError(f"Fehler beim Laden von polls.tsv: {e}")
    
    # 2. Filtere und parse finalisierte Polls
    polls = filter_and_parse_polls(raw_polls, calculated_at)
    
    if not polls:
        logger.warning("Keine finalisierten Polls gefunden - leere Berechnung")
        return
    
    # 3. Delegiere an I/O-freie Funktion
    run_rating_update_from_polls(polls, ratings_path, calculated_at)

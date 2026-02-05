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

Siehe auch: docs/bradley_terry_research.md
"""

import csv
from pathlib import Path
from typing import List, Dict, Tuple, Set
from datetime import datetime, timezone
from collections import defaultdict
import logging

import choix
import numpy as np

from bot.logger import get_logger

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


def load_finalized_polls(polls_path: Path, calculated_at: datetime) -> List[Dict]:
    """
    Lädt finalisierte Polls aus polls.tsv.
    
    Nur Polls mit finalized_at <= calculated_at werden berücksichtigt.
    Polls mit votes_a + votes_b == 0 werden geloggt und ignoriert.
    
    Args:
        polls_path: Pfad zu polls.tsv
        calculated_at: Cutoff-Zeit für finalisierte Polls (UTC)
        
    Returns:
        Liste von Poll-Dictionaries mit parseten Integer-Werten
        
    Raises:
        BradleyTerryError: Bei fehlenden/kaputten Spalten oder Parse-Fehlern
    """
    if not polls_path.exists():
        raise BradleyTerryError(f"polls.tsv nicht gefunden: {polls_path}")
    
    try:
        with open(polls_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            if reader.fieldnames is None:
                raise BradleyTerryError("Keine Header in polls.tsv gefunden")
            
            # Validiere erforderliche Spalten
            required_cols = ['episode_a_id', 'episode_b_id', 'votes_a', 'votes_b', 'finalized_at']
            missing_cols = [col for col in required_cols if col not in reader.fieldnames]
            if missing_cols:
                raise BradleyTerryError(
                    f"Fehlende Spalten in polls.tsv: {missing_cols}"
                )
            
            all_polls = list(reader)
            logger.info(f"Polls geladen: {len(all_polls)} Einträge")
            
            finalized_polls = []
            zero_vote_count = 0
            
            for poll in all_polls:
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
            
    except csv.Error as e:
        raise BradleyTerryError(f"CSV-Fehler beim Laden von polls.tsv: {e}")
    except BradleyTerryError:
        raise
    except Exception as e:
        raise BradleyTerryError(f"Unerwarteter Fehler beim Laden von polls.tsv: {e}")


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
    
    Verwendet BFS (Breadth-First Search).
    
    Args:
        graph: Adjazenzliste
        start_node: Startknoten (Episode-ID)
        
    Returns:
        Set von Episode-IDs in der Zusammenhangskomponente
    """
    if start_node not in graph:
        return set()
    
    visited = set()
    queue = [start_node]
    
    while queue:
        node = queue.pop(0)
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


def prepare_pairwise_data(polls: List[Dict], episode_ids: List[int]) -> np.ndarray:
    """
    Bereitet Paarvergleichsdaten für choix auf.
    
    Args:
        polls: Liste von Poll-Dictionaries
        episode_ids: Sortierte Liste von Episode-IDs (für Index-Mapping)
        
    Returns:
        numpy array mit shape (n_comparisons, 4) - [winner_idx, loser_idx, win_count, lose_count]
        Jeder Poll wird als Binomial-Count behandelt
    """
    # Mapping: episode_id -> index
    id_to_idx = {ep_id: idx for idx, ep_id in enumerate(episode_ids)}
    
    # Liste für alle Vergleiche (jeder Poll trägt zu beiden Richtungen bei)
    comparisons = []
    
    for poll in polls:
        idx_a = id_to_idx[poll['episode_a_id']]
        idx_b = id_to_idx[poll['episode_b_id']]
        votes_a = poll['votes_a']
        votes_b = poll['votes_b']
        
        # Füge beide Richtungen hinzu (für choix Binomial-Format)
        # Format: [winner_idx, loser_idx, win_votes, lose_votes]
        # Wir nutzen hier das Format: beide Richtungen separat
        if votes_a > 0:
            comparisons.append([idx_a, idx_b, votes_a, votes_b])
        if votes_b > 0:
            comparisons.append([idx_b, idx_a, votes_b, votes_a])
    
    return np.array(comparisons, dtype=int)


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
    data: np.ndarray,
    alpha: float = 0.01,
    max_iter: int = 10000,
    tol: float = 1e-6
) -> np.ndarray:
    """
    Fit't das Bradley-Terry-Modell mit MM-Algorithmus.
    
    Args:
        data: Pairwise comparison data (n_comparisons x 4)
        alpha: L2-Regularisierungsstärke
        max_iter: Maximale Iterationen
        tol: Konvergenztoleranz
        
    Returns:
        Log-Stärken theta (n_items,)
        
    Raises:
        BradleyTerryError: Bei Konvergenzfehlern
    """
    try:
        # choix erwartet data im Format (winner, loser) für jede Observation
        # Wir müssen die Daten expandieren: votes_a Beobachtungen für A > B
        expanded_data = []
        for row in data:
            winner_idx, loser_idx, win_votes, _ = row
            for _ in range(win_votes):
                expanded_data.append((winner_idx, loser_idx))
        
        # Konvertiere zu numpy array
        expanded_data = np.array(expanded_data, dtype=int)
        
        # Fit Bradley-Terry mit MM
        theta = choix.mm_pairwise(
            n_items=len(set(expanded_data.flatten())),
            data=expanded_data,
            alpha=alpha,
            max_iter=max_iter,
            tol=tol
        )
        
        return theta
        
    except Exception as e:
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


def append_ratings_to_tsv(
    ratings_path: Path,
    episode_ids: List[int],
    utilities: np.ndarray,
    matches: Dict[int, int],
    calculated_at: datetime
) -> None:
    """
    Hängt neue Ratings an ratings.tsv an (append-only).
    
    Format: episode_id, utility, matches, calculated_at
    
    Args:
        ratings_path: Pfad zu ratings.tsv
        episode_ids: Liste von Episode-IDs (sortiert)
        utilities: Entsprechende Utilities
        matches: Match-Counts pro Episode
        calculated_at: Timestamp der Berechnung (UTC)
        
    Raises:
        BradleyTerryError: Bei Schreibfehlern
    """
    try:
        # Prüfe ob Datei existiert und Header vorhanden ist
        file_exists = ratings_path.exists()
        
        with open(ratings_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            
            # Schreibe Header nur wenn Datei neu ist
            if not file_exists:
                writer.writerow(['episode_id', 'utility', 'matches', 'calculated_at'])
            
            # Schreibe Ratings (sortiert nach episode_id)
            timestamp_str = calculated_at.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            for ep_id, utility in zip(episode_ids, utilities):
                match_count = matches[ep_id]
                writer.writerow([
                    ep_id,
                    f"{utility:.6f}",
                    match_count,
                    timestamp_str
                ])
        
        logger.info(f"Ratings für {len(episode_ids)} Episoden geschrieben nach {ratings_path}")
        
    except Exception as e:
        raise BradleyTerryError(f"Fehler beim Schreiben von ratings.tsv: {e}")


def run_rating_update(
    polls_path: Path,
    ratings_path: Path,
    calculated_at: datetime = None
) -> None:
    """
    Führt ein vollständiges Bradley-Terry Rating-Update durch.
    
    Ablauf:
    1. Lade finalisierte Polls
    2. Baue Konnektivitätsgraph
    3. Finde Komponente mit Episode 1
    4. Filtere Polls und Episoden
    5. Bereite Daten für choix vor
    6. Fitte Bradley-Terry-Modell
    7. Berechne normierte Utilities
    8. Append zu ratings.tsv
    
    Args:
        polls_path: Pfad zu polls.tsv
        ratings_path: Pfad zu ratings.tsv
        calculated_at: Optional - UTC-Zeitpunkt der Berechnung (default: jetzt)
        
    Raises:
        BradleyTerryError: Bei allen kritischen Fehlern
    """
    # Bestimme calculated_at
    if calculated_at is None:
        calculated_at = datetime.now(timezone.utc)
    
    logger.info(f"=== Bradley-Terry Rating Update ===")
    logger.info(f"Calculated at: {calculated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # 1. Lade finalisierte Polls
    polls = load_finalized_polls(polls_path, calculated_at)
    
    if not polls:
        logger.warning("Keine finalisierten Polls gefunden - leere Berechnung")
        return
    
    # 2. Baue Graph
    logger.info("Baue Konnektivitätsgraph...")
    graph = build_connectivity_graph(polls)
    logger.info(f"Graph enthält {len(graph)} Episoden")
    
    # 3. Finde Komponente mit Episode 1
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
    
    # 4. Filtere Polls
    filtered_polls = filter_polls_by_episodes(polls, connected_episodes)
    logger.info(f"Polls nach Filterung: {len(filtered_polls)}")
    
    # 5. Sortiere Episode-IDs für konsistente Indizierung
    episode_ids = sorted(list(connected_episodes))
    logger.info(f"Episoden im Modell: {len(episode_ids)}")
    
    # 6. Bereite Daten vor
    pairwise_data = prepare_pairwise_data(filtered_polls, episode_ids)
    logger.info(f"Pairwise comparisons: {len(pairwise_data)}")
    
    # 7. Zähle Matches
    match_counts = count_matches_per_episode(filtered_polls, episode_ids)
    
    # 8. Fitte Modell
    logger.info("Fitte Bradley-Terry-Modell (MM, alpha=0.01)...")
    theta = fit_bradley_terry_model(pairwise_data, alpha=0.01)
    logger.info(f"Modell konvergiert, theta shape: {theta.shape}")
    
    # 9. Normiere Utilities
    utilities = normalize_utilities(theta)
    logger.info(f"Utilities berechnet - mean: {np.mean(utilities):.6f}, std: {np.std(utilities):.6f}")
    
    # 10. Schreibe zu ratings.tsv
    append_ratings_to_tsv(ratings_path, episode_ids, utilities, match_counts, calculated_at)
    
    # Finale Metriken
    logger.info(f"=== Update abgeschlossen ===")
    logger.info(f"Verwendete Polls: {len(filtered_polls)}")
    logger.info(f"Gerankte Episoden: {len(episode_ids)}")
    logger.info(f"Gedroppte Episoden: {len(dropped_episodes)}")

"""
Matchmaking fuer neue Poll-Paare.

Dieses Modul waehlt das naechste Folgenpaar fuer einen neuen Poll aus.
Der Kern ist I/O-frei (`select_next_match_from_data`) und nimmt bereits
geladene Datenstrukturen entgegen. Ein schlanker Wrapper (`select_next_match`)
laedt die Daten aus den Repository-Dateien.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from bot.dreimetadaten_api import fetch_all_episodes
from bot.logger import get_logger
from bot.tsv_repository import load_polls, load_ratings, TSVError

logger = get_logger(__name__)


class MatchmakingError(Exception):
    """Exception fuer Matchmaking-Fehler."""


def _normalize_pair(a: int, b: int) -> Tuple[int, int]:
    return (a, b) if a < b else (b, a)


def _parse_poll_pair(poll: Dict[str, Any]) -> Tuple[int, int]:
    try:
        episode_a = int(poll['episode_a_id'])
        episode_b = int(poll['episode_b_id'])
    except (KeyError, ValueError, TypeError) as exc:
        raise MatchmakingError(f"Ungueltige Poll-Zeile fuer Matchmaking: {poll}") from exc

    if episode_a == episode_b:
        raise MatchmakingError(f"Ungueltiger Poll mit identischen Episoden: {poll}")

    return _normalize_pair(episode_a, episode_b)


def _seed_pairs(k_seed: int) -> List[Tuple[int, int]]:
    if k_seed != 8:
        raise MatchmakingError("Aktuell ist nur K_seed=8 implementiert")
    return [
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 8),
        (1, 8),
    ]


def _latest_rating_by_episode(rating_rows: List[Dict[str, Any]]) -> Dict[int, Dict[str, float]]:
    latest: Dict[int, Tuple[str, Dict[str, float]]] = {}

    for row in rating_rows:
        try:
            episode_id = int(row['episode_id'])
            utility = float(row['utility'])
            std_error = float(row['std_error'])
            calculated_at = str(row['calculated_at'])
        except (KeyError, ValueError, TypeError):
            continue

        current = latest.get(episode_id)
        payload = {'utility': utility, 'std_error': std_error}
        if current is None or calculated_at > current[0]:
            latest[episode_id] = (calculated_at, payload)

    return {episode_id: data for episode_id, (_, data) in latest.items()}


def _episode_ids_from_api() -> List[int]:
    episodes = fetch_all_episodes()
    ids = sorted(int(row['nummer']) for row in episodes)
    if not ids:
        raise MatchmakingError("Keine Episoden von der API erhalten")
    return ids


def _build_active_set(
    episode_ids: List[int],
    finalized_pairs: List[Tuple[int, int]],
    k_seed: int,
    frontier_size: int,
) -> Tuple[Set[int], Set[int]]:
    activated: Set[int] = {episode_id for episode_id in episode_ids if 1 <= episode_id <= k_seed}

    for episode_a, episode_b in finalized_pairs:
        if episode_a in episode_ids and episode_a > k_seed:
            activated.add(episode_a)
        if episode_b in episode_ids and episode_b > k_seed:
            activated.add(episode_b)

    remaining = [episode_id for episode_id in episode_ids if episode_id not in activated]
    frontier = set(remaining[:frontier_size])
    active_set = activated.union(frontier)
    return active_set, activated


def select_next_match_from_data(
    episode_ids: List[int],
    finalized_polls: List[Dict[str, Any]],
    running_polls: List[Dict[str, Any]],
    rating_rows: Optional[List[Dict[str, Any]]] = None,
    k_seed: int = 8,
    frontier_size: int = 4,
    d_min: int = 6,
    min_anchor_for_uncal_vs_uncal: int = 1,
    tau_rec: float = 4.0,
    k_candidates: int = 100,
    temperature: float = 0.3,
    epsilon: float = 0.05,
    random_seed: int = 42,
) -> Tuple[int, int]:
    """
    Waehlt das naechste Paar fuer einen neuen Poll.

    Args:
        episode_ids: Sortierte Liste verfuegbarer Episoden-IDs
        finalized_polls: Bereits abgeschlossene Polls
        running_polls: Aktuell laufende Polls (werden ausgeschlossen)
        rating_rows: Optional, Zeilen aus ratings.tsv (fuer utility/std_error)

    Returns:
        Tuple (episode_a_id, episode_b_id)

    Raises:
        MatchmakingError: Wenn kein gueltiges Paar gefunden werden kann
    """
    if not episode_ids:
        raise MatchmakingError("episode_ids darf nicht leer sein")

    episode_ids = sorted(set(int(ep) for ep in episode_ids))
    episode_set = set(episode_ids)
    finalized_pairs = [_parse_poll_pair(poll) for poll in finalized_polls]
    running_pairs = {_parse_poll_pair(poll) for poll in running_polls}
    pair_history: Dict[Tuple[int, int], int] = {}

    for pair in finalized_pairs:
        pair_history[pair] = pair_history.get(pair, 0) + 1

    # Seed-Phase: feste Reihenfolge
    for seed_pair in _seed_pairs(k_seed):
        if seed_pair[0] not in episode_set or seed_pair[1] not in episode_set:
            continue
        if pair_history.get(seed_pair, 0) == 0 and seed_pair not in running_pairs:
            logger.info(f"Matchmaking Seed-Phase: waehle Paar {seed_pair}")
            return seed_pair

    active_set, _activated = _build_active_set(
        episode_ids=episode_ids,
        finalized_pairs=finalized_pairs,
        k_seed=k_seed,
        frontier_size=frontier_size,
    )

    blocked_episodes: Set[int] = set()
    for episode_a, episode_b in running_pairs:
        blocked_episodes.add(episode_a)
        blocked_episodes.add(episode_b)

    candidate_episode_ids = sorted(active_set - blocked_episodes)
    if len(candidate_episode_ids) < 2:
        raise MatchmakingError("Keine freie Episode fuer neues Paar verfuegbar")

    n_total = {episode_id: 0 for episode_id in episode_ids}
    last_seen_poll_idx = {episode_id: -1 for episode_id in episode_ids}
    calib_matches = {episode_id: 0 for episode_id in episode_ids}

    for idx, (episode_a, episode_b) in enumerate(finalized_pairs):
        if episode_a in n_total:
            n_total[episode_a] += 1
            last_seen_poll_idx[episode_a] = idx
        if episode_b in n_total:
            n_total[episode_b] += 1
            last_seen_poll_idx[episode_b] = idx

    calibrated_now = {episode_id for episode_id, count in n_total.items() if count >= d_min}
    for episode_a, episode_b in finalized_pairs:
        if episode_a not in episode_set or episode_b not in episode_set:
            continue
        if episode_a not in calibrated_now and episode_b in calibrated_now:
            calib_matches[episode_a] += 1
        if episode_b not in calibrated_now and episode_a in calibrated_now:
            calib_matches[episode_b] += 1

    ratings = _latest_rating_by_episode(rating_rows or [])

    # Fallback falls std_error/utility fehlen
    utility = {episode_id: ratings.get(episode_id, {}).get('utility', 1.0) for episode_id in episode_ids}
    raw_unc: Dict[int, float] = {}
    for episode_id in episode_ids:
        if episode_id in ratings:
            raw_unc[episode_id] = float(ratings[episode_id]['std_error'])
        else:
            raw_unc[episode_id] = float(1.0 / np.sqrt(n_total[episode_id] + 1.0))

    unc_values = [raw_unc[episode_id] for episode_id in candidate_episode_ids]
    unc_min = min(unc_values)
    unc_max = max(unc_values)
    if unc_max > unc_min:
        unc_norm = {
            episode_id: (raw_unc[episode_id] - unc_min) / (unc_max - unc_min)
            for episode_id in episode_ids
        }
    else:
        unc_norm = {episode_id: 0.0 for episode_id in episode_ids}

    poll_count = len(finalized_pairs)

    def recency_score(episode_id: int) -> float:
        last_seen = last_seen_poll_idx.get(episode_id, -1)
        age = poll_count + 10 if last_seen < 0 else max(0, poll_count - last_seen)
        return 1.0 - float(np.exp(-age / tau_rec))

    eligible: List[Tuple[int, int]] = []
    scores: List[float] = []

    for idx, episode_a in enumerate(candidate_episode_ids):
        for episode_b in candidate_episode_ids[idx + 1:]:
            pair = _normalize_pair(episode_a, episode_b)

            if pair in running_pairs:
                continue

            # Hard Constraint: no unobserved vs unobserved
            if n_total[episode_a] == 0 and n_total[episode_b] == 0:
                continue

            calibrated_a = n_total[episode_a] >= d_min and calib_matches[episode_a] >= 2
            calibrated_b = n_total[episode_b] >= d_min and calib_matches[episode_b] >= 2

            # Gate fuer uncalibrated vs uncalibrated
            if not calibrated_a and not calibrated_b and n_total[episode_a] > 0 and n_total[episode_b] > 0:
                if calib_matches[episode_a] < min_anchor_for_uncal_vs_uncal:
                    continue
                if calib_matches[episode_b] < min_anchor_for_uncal_vs_uncal:
                    continue

            p_ij = 1.0 / (1.0 + np.exp(-(utility[episode_a] - utility[episode_b])))
            s_close = 1.0 - 2.0 * abs(p_ij - 0.5)
            s_unc = 0.5 * (unc_norm[episode_a] + unc_norm[episode_b])
            s_rec = 0.5 * (recency_score(episode_a) + recency_score(episode_b))
            s_cal = 1.0 if calibrated_a != calibrated_b else 0.0

            repeat_count = pair_history.get(pair, 0)
            repeat_penalty = repeat_count / (repeat_count + 1.0)

            score = (
                0.2 * s_close
                + 0.6 * s_unc
                + 1.0 * s_cal
                + 0.4 * s_rec
                - 1.5 * repeat_penalty
            )

            eligible.append(pair)
            scores.append(score)

    if not eligible:
        raise MatchmakingError("Kein geeignetes Paar fuer den naechsten Poll gefunden")

    # Top-K Kandidaten
    ranked_indices = np.argsort(np.array(scores))[::-1]
    top_indices = ranked_indices[: min(k_candidates, len(ranked_indices))]

    top_pairs = [eligible[i] for i in top_indices]
    top_scores = np.array([scores[i] for i in top_indices], dtype=float)

    rng = np.random.default_rng(random_seed + poll_count)

    # epsilon-Exploration
    if epsilon > 0 and rng.random() < epsilon:
        random_idx = int(rng.integers(0, len(eligible)))
        return eligible[random_idx]

    # Softmax-Auswahl
    shifted = top_scores - np.max(top_scores)
    logits = shifted / max(temperature, 1e-6)
    weights = np.exp(logits)
    probabilities = weights / np.sum(weights)

    chosen_idx = int(rng.choice(len(top_pairs), p=probabilities))
    return top_pairs[chosen_idx]


def select_next_match(
    polls_path: Path,
    ratings_path: Path,
    running_polls: Optional[List[Dict[str, Any]]] = None,
    episode_ids: Optional[List[int]] = None,
) -> Tuple[int, int]:
    """
    Wrapper mit Dateizugriff fuer produktiven Einsatz.

    Args:
        polls_path: Pfad zu polls.tsv
        ratings_path: Pfad zu ratings.tsv
        running_polls: Optional explizite laufende Polls (falls bereits bekannt)
        episode_ids: Optional Episodenliste, sonst API-Abruf
    """
    try:
        raw_polls = load_polls(polls_path)
        rating_rows = load_ratings(ratings_path)
    except TSVError as exc:
        raise MatchmakingError(f"Fehler beim Laden der TSV-Daten: {exc}") from exc

    if episode_ids is None:
        episode_ids = _episode_ids_from_api()

    finalized_polls = []
    inferred_running_polls = []

    now = datetime.now(timezone.utc)
    for poll in raw_polls:
        finalized_at = str(poll.get('finalized_at', '')).strip()
        if finalized_at:
            finalized_polls.append(poll)
            continue

        closes_at_raw = str(poll.get('closes_at', '')).strip()
        if not closes_at_raw:
            inferred_running_polls.append(poll)
            continue

        try:
            closes_at = datetime.fromisoformat(closes_at_raw.replace('Z', '+00:00'))
            if closes_at.tzinfo is None:
                closes_at = closes_at.replace(tzinfo=timezone.utc)
            else:
                closes_at = closes_at.astimezone(timezone.utc)
            if closes_at > now:
                inferred_running_polls.append(poll)
        except ValueError:
            inferred_running_polls.append(poll)

    return select_next_match_from_data(
        episode_ids=episode_ids,
        finalized_polls=finalized_polls,
        running_polls=running_polls if running_polls is not None else inferred_running_polls,
        rating_rows=rating_rows,
    )

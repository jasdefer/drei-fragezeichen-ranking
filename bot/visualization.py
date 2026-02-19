"""
Erstellung einer statischen Visualisierung fuer GitHub Pages.

Dieses Modul transformiert ratings.tsv in ein JSON-Format fuer das Frontend
und kopiert statische Assets in einen Build-Ordner.
"""

from __future__ import annotations

import json
import statistics
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from bot.bradley_terry import BradleyTerryError, filter_and_parse_polls, run_rating_update_from_polls
from bot.dreimetadaten_api import APIError, fetch_all_episode_metadata
from bot.logger import get_logger
from bot.matchmaking import MatchmakingError, get_next_match_candidates_from_data
from bot.tsv_repository import load_polls, load_ratings, TSVError

logger = get_logger(__name__)


class VisualizationError(Exception):
    """Exception fuer Visualisierungs-Build-Fehler."""


def _parse_utc_timestamp(timestamp: str) -> datetime:
    """Parst UTC-ISO-8601 mit Z-Suffix in ein timezone-aware datetime."""
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as e:
        raise VisualizationError(f"Ungueltiger calculated_at Timestamp: {timestamp}") from e

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _get_latest_calculated_at(rating_rows: List[Dict[str, str]]) -> Optional[datetime]:
    """Liest den neuesten calculated_at Timestamp aus rohen Rating-Zeilen."""
    if not rating_rows:
        return None

    parsed_timestamps: List[datetime] = []
    for row in rating_rows:
        calculated_at = row.get("calculated_at")
        if not calculated_at:
            continue
        parsed_timestamps.append(_parse_utc_timestamp(calculated_at))

    if not parsed_timestamps:
        return None

    return max(parsed_timestamps)


def update_ratings_from_polls_if_needed(polls_file: Path, ratings_file: Path) -> bool:
    """
    Aktualisiert ratings.tsv aus polls.tsv, wenn neue finalisierte Polls existieren.

    Es wird nur geschrieben, wenn mindestens ein Poll mit finalized_at > letztem
    calculated_at in ratings.tsv vorhanden ist. Die eigentliche BT-Berechnung nutzt
    dann weiterhin alle finalisierten Polls bis zum aktuellen Zeitpunkt.

    Returns:
        True, wenn ein neues Rating-Snapshot geschrieben wurde, sonst False.

    Raises:
        VisualizationError: Bei Parse-/Berechnungsfehlern
        TSVError: Bei TSV-Lade-/Schreibfehlern
    """
    now_utc = datetime.now(timezone.utc)

    raw_ratings = load_ratings(ratings_file)
    latest_calculated_at = _get_latest_calculated_at(raw_ratings)

    raw_polls = load_polls(polls_file)

    try:
        finalized_polls = filter_and_parse_polls(raw_polls, now_utc)
    except BradleyTerryError as e:
        raise VisualizationError(f"Fehler beim Parsen der Polls fuer Update: {e}") from e

    if not finalized_polls:
        logger.info("Keine finalisierten Polls vorhanden - ratings.tsv bleibt unveraendert")
        return False

    if latest_calculated_at is not None:
        has_new_polls = any(
            poll["finalized_at"] > latest_calculated_at for poll in finalized_polls
        )
        if not has_new_polls:
            logger.info(
                "Keine neuen finalisierten Polls seit %s - ratings.tsv bleibt unveraendert",
                latest_calculated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
            return False

    try:
        run_rating_update_from_polls(
            polls=finalized_polls,
            ratings_path=ratings_file,
            calculated_at=now_utc,
        )
    except BradleyTerryError as e:
        raise VisualizationError(f"Fehler beim Aktualisieren von ratings.tsv: {e}") from e

    logger.info("ratings.tsv wurde aus polls.tsv aktualisiert")
    return True


def _normalize_rating_row(row: Dict[str, str]) -> Dict[str, Any]:
    """Konvertiert eine TSV-Rating-Zeile in getypte Werte."""
    try:
        episode_id = int(row["episode_id"])
        utility = float(row["utility"])
        std_error = float(row["std_error"])
        poll_count = int(row["poll_count"])
        calculated_at = _parse_utc_timestamp(row["calculated_at"])
    except KeyError as e:
        raise VisualizationError(f"Fehlendes Feld in Rating-Zeile: {e}") from e
    except ValueError as e:
        raise VisualizationError(f"Ungueltiger Zahlenwert in Rating-Zeile: {e}") from e

    return {
        "episode_id": episode_id,
        "utility": utility,
        "std_error": std_error,
        "poll_count": poll_count,
        "calculated_at": calculated_at,
    }


def _serialize_episode_metadata(metadata_rows: Optional[List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """Serialisiert API-Metadaten in ein robustes Dict nach episode_id."""
    serialized: Dict[str, Dict[str, Any]] = {}
    for row in metadata_rows or []:
        try:
            episode_id = int(row["nummer"])
        except (KeyError, TypeError, ValueError):
            continue

        serialized[str(episode_id)] = {
            "episode_id": episode_id,
            "title": str(row.get("titel") or "").strip(),
            "description": str(
                row.get("kurzbeschreibung") or row.get("beschreibung") or ""
            ).strip(),
            "cover_url": str(row.get("urlCoverApple") or "").strip(),
        }

    return serialized


def _parse_optional_timestamp(timestamp_raw: str) -> Optional[datetime]:
    if not timestamp_raw:
        return None
    try:
        return _parse_utc_timestamp(timestamp_raw)
    except VisualizationError:
        return None


def _build_open_polls(raw_polls: List[Dict[str, str]], now_utc: datetime) -> List[Dict[str, Any]]:
    """Erzeugt Liste laufender/offener Polls fuer Dashboard-Overview."""
    open_polls: List[Dict[str, Any]] = []

    for poll in raw_polls:
        finalized_at_raw = str(poll.get("finalized_at") or "").strip()
        if finalized_at_raw:
            continue

        try:
            poll_id = int(poll.get("poll_id") or 0)
            episode_a_id = int(poll["episode_a_id"])
            episode_b_id = int(poll["episode_b_id"])
        except (KeyError, TypeError, ValueError):
            continue

        closes_at_raw = str(poll.get("closes_at") or "").strip()
        closes_at = _parse_optional_timestamp(closes_at_raw)

        status = "unknown_close"
        closes_in_hours: Optional[float] = None
        if closes_at is not None:
            delta_seconds = (closes_at - now_utc).total_seconds()
            closes_in_hours = round(delta_seconds / 3600.0, 1)
            status = "open" if delta_seconds > 0 else "pending_finalization"

        open_polls.append(
            {
                "poll_id": poll_id,
                "reddit_post_id": str(poll.get("reddit_post_id") or "").strip(),
                "episode_a_id": episode_a_id,
                "episode_b_id": episode_b_id,
                "created_at": str(poll.get("created_at") or "").strip(),
                "closes_at": closes_at_raw,
                "status": status,
                "closes_in_hours": closes_in_hours,
            }
        )

    open_polls.sort(key=lambda item: (item["status"] != "open", item["poll_id"]))
    return open_polls


def _collect_episode_ids(
    normalized_rows: List[Dict[str, Any]],
    raw_polls: List[Dict[str, str]],
    episode_metadata_by_id: Dict[str, Dict[str, Any]],
) -> List[int]:
    """Sammelt verfuegbare Episode-IDs fuer Matchmaking-Prognosen."""
    episode_ids = {row["episode_id"] for row in normalized_rows}

    for poll in raw_polls:
        try:
            episode_ids.add(int(poll["episode_a_id"]))
            episode_ids.add(int(poll["episode_b_id"]))
        except (KeyError, TypeError, ValueError):
            continue

    for episode_id_string in episode_metadata_by_id.keys():
        try:
            episode_ids.add(int(episode_id_string))
        except ValueError:
            continue

    return sorted(episode_ids)


def _build_poll_analytics(raw_polls: List[Dict[str, str]], now_utc: datetime) -> Dict[str, Any]:
    """Berechnet Poll-Listen, Top-10 und Stimmenmetriken fuer das Dashboard."""
    all_polls: List[Dict[str, Any]] = []
    finalized_polls: List[Dict[str, Any]] = []
    votes_per_episode: Dict[int, List[int]] = {}

    for poll in raw_polls:
        try:
            poll_id = int(str(poll.get("poll_id") or "0"))
            episode_a_id = int(str(poll.get("episode_a_id") or "0"))
            episode_b_id = int(str(poll.get("episode_b_id") or "0"))
            votes_a = int(str(poll.get("votes_a") or "0"))
            votes_b = int(str(poll.get("votes_b") or "0"))
        except (TypeError, ValueError):
            continue

        created_at = str(poll.get("created_at") or "").strip()
        closes_at = str(poll.get("closes_at") or "").strip()
        finalized_at = str(poll.get("finalized_at") or "").strip()
        closes_dt = _parse_optional_timestamp(closes_at)

        status = "unknown_close"
        if finalized_at:
            status = "finalized"
        elif closes_dt is not None:
            status = "open" if closes_dt > now_utc else "pending_finalization"

        total_votes = votes_a + votes_b
        vote_margin = abs(votes_a - votes_b)

        poll_item = {
            "poll_id": poll_id,
            "reddit_post_id": str(poll.get("reddit_post_id") or "").strip(),
            "episode_a_id": episode_a_id,
            "episode_b_id": episode_b_id,
            "votes_a": votes_a,
            "votes_b": votes_b,
            "total_votes": total_votes,
            "vote_margin": vote_margin,
            "created_at": created_at,
            "closes_at": closes_at,
            "finalized_at": finalized_at,
            "status": status,
        }

        all_polls.append(poll_item)

        if finalized_at:
            finalized_polls.append(poll_item)
            votes_per_episode.setdefault(episode_a_id, []).append(total_votes)
            votes_per_episode.setdefault(episode_b_id, []).append(total_votes)

    all_polls.sort(key=lambda item: (item["poll_id"], item["created_at"]), reverse=True)
    finalized_polls.sort(key=lambda item: (item["finalized_at"], item["poll_id"]))

    total_votes = sum(poll["total_votes"] for poll in finalized_polls)
    avg_votes_per_poll = (
        total_votes / len(finalized_polls) if finalized_polls else None
    )
    median_votes_per_poll = (
        statistics.median(poll["total_votes"] for poll in finalized_polls)
        if finalized_polls
        else None
    )

    return {
        "all_polls": all_polls,
        "finalized_polls": finalized_polls,
        "votes_per_episode": votes_per_episode,
        "total_votes": total_votes,
        "avg_votes_per_poll": avg_votes_per_poll,
        "median_votes_per_poll": median_votes_per_poll,
    }


def _build_ranked_poll_views(
    finalized_polls: List[Dict[str, Any]],
    ranked_episode_ids: List[int],
    rank_by_episode: Dict[int, int],
) -> Dict[str, List[Dict[str, Any]]]:
    """Berechnet Trend/Top-Listen nur fuer aktuell gerankte Episoden."""
    ranked_set = set(ranked_episode_ids)
    ranked_polls = [
        poll
        for poll in finalized_polls
        if poll["episode_a_id"] in ranked_set and poll["episode_b_id"] in ranked_set
    ]

    enriched_ranked_polls: List[Dict[str, Any]] = []
    for poll in ranked_polls:
        enriched = dict(poll)
        rank_a = rank_by_episode.get(poll["episode_a_id"])
        rank_b = rank_by_episode.get(poll["episode_b_id"])
        enriched["rank_a"] = rank_a
        enriched["rank_b"] = rank_b
        if rank_a is not None and rank_b is not None:
            enriched["avg_pair_rank"] = (rank_a + rank_b) / 2.0
        else:
            enriched["avg_pair_rank"] = None
        enriched_ranked_polls.append(enriched)

    top_exciting_polls = sorted(
        enriched_ranked_polls,
        key=lambda item: (
            item["vote_margin"],
            -item["total_votes"],
            item["avg_pair_rank"] if item["avg_pair_rank"] is not None else 9999,
            -item["poll_id"],
        ),
    )[:10]

    top_reach_polls = sorted(
        enriched_ranked_polls,
        key=lambda item: (
            -item["total_votes"],
            item["avg_pair_rank"] if item["avg_pair_rank"] is not None else 9999,
            item["vote_margin"],
            -item["poll_id"],
        ),
    )[:10]

    votes_trend = [
        {
            "poll_id": poll["poll_id"],
            "finalized_at": poll["finalized_at"],
            "total_votes": poll["total_votes"],
            "episode_a_id": poll["episode_a_id"],
            "episode_b_id": poll["episode_b_id"],
            "rank_a": poll.get("rank_a"),
            "rank_b": poll.get("rank_b"),
            "avg_pair_rank": poll.get("avg_pair_rank"),
        }
        for poll in sorted(enriched_ranked_polls, key=lambda item: (item["finalized_at"], item["poll_id"]))
    ]

    return {
        "top_exciting_polls": top_exciting_polls,
        "top_reach_polls": top_reach_polls,
        "votes_trend": votes_trend,
    }


def _build_episode_engagement_cards(
    ranking_rows: List[Dict[str, Any]],
    votes_per_episode: Dict[int, List[int]],
) -> List[Dict[str, Any]]:
    """Berechnet Engagement-Karten je gerankter Folge."""
    cards: List[Dict[str, Any]] = []
    for row in ranking_rows:
        episode_votes = votes_per_episode.get(row["episode_id"], [])
        avg_votes = (
            sum(episode_votes) / len(episode_votes) if episode_votes else None
        )
        median_votes = statistics.median(episode_votes) if episode_votes else None

        cards.append(
            {
                "rank": row["rank"],
                "episode_id": row["episode_id"],
                "utility": row["utility"],
                "std_error": row["std_error"],
                "poll_count": row["poll_count"],
                "avg_votes_per_poll": avg_votes,
                "median_votes_per_poll": median_votes,
                "total_votes": sum(episode_votes),
                "finalized_poll_count": len(episode_votes),
            }
        )

    return cards


def build_visualization_payload(
    rating_rows: List[Dict[str, str]],
    raw_polls: Optional[List[Dict[str, str]]] = None,
    metadata_rows: Optional[List[Dict[str, Any]]] = None,
    metadata_warning: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Erzeugt das Frontend-JSON aus rohen TSV-Rating-Zeilen.

    Returns:
        Dict mit Ranking (aktueller Stand), Historie und Metainformationen.
    """
    now_utc = datetime.now(timezone.utc)
    normalized_rows = [_normalize_rating_row(row) for row in rating_rows]
    episode_metadata_by_id = _serialize_episode_metadata(metadata_rows)
    metadata_available = len(episode_metadata_by_id) > 0
    polls = raw_polls or []
    open_polls = _build_open_polls(polls, now_utc)
    poll_analytics = _build_poll_analytics(polls, now_utc)

    if not normalized_rows:
        return {
            "has_rankings": False,
            "generated_at": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latest_calculated_at": None,
            "ranking": [],
            "history_by_episode": {},
            "episode_ids": [],
            "metadata_available": metadata_available,
            "metadata_warning": metadata_warning,
            "episode_metadata_by_id": episode_metadata_by_id,
            "open_polls": open_polls,
            "all_polls": poll_analytics["all_polls"],
            "top_exciting_polls": [],
            "top_reach_polls": [],
            "votes_trend": [],
            "episode_engagement_cards": [],
            "next_match_candidates": [],
            "next_match_candidates_provisional": True,
            "kpis": {
                "ranked_episodes": 0,
                "open_polls": len(open_polls),
                "avg_std_error": None,
                "avg_poll_count": None,
                "total_votes": poll_analytics["total_votes"],
                "avg_votes_per_poll": poll_analytics["avg_votes_per_poll"],
                "median_votes_per_poll": poll_analytics["median_votes_per_poll"],
            },
        }

    history_by_episode: Dict[int, List[Dict[str, Any]]] = {}
    for row in normalized_rows:
        episode_id = row["episode_id"]
        history_by_episode.setdefault(episode_id, []).append(row)

    for episode_history in history_by_episode.values():
        episode_history.sort(key=lambda item: item["calculated_at"])

    latest_by_episode: Dict[int, Dict[str, Any]] = {
        episode_id: history[-1] for episode_id, history in history_by_episode.items()
    }

    ranking_rows = sorted(
        latest_by_episode.values(),
        key=lambda item: (-item["utility"], item["episode_id"]),
    )

    ranking: List[Dict[str, Any]] = []
    for index, row in enumerate(ranking_rows, start=1):
        ranking.append(
            {
                "rank": index,
                "episode_id": row["episode_id"],
                "utility": row["utility"],
                "std_error": row["std_error"],
                "poll_count": row["poll_count"],
                "calculated_at": row["calculated_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )

    rank_by_episode = {item["episode_id"]: item["rank"] for item in ranking}
    ranked_poll_views = _build_ranked_poll_views(
        finalized_polls=poll_analytics["finalized_polls"],
        ranked_episode_ids=[item["episode_id"] for item in ranking],
        rank_by_episode=rank_by_episode,
    )

    history_serialized: Dict[str, List[Dict[str, Any]]] = {}
    for episode_id, episode_history in history_by_episode.items():
        history_serialized[str(episode_id)] = [
            {
                "episode_id": row["episode_id"],
                "utility": row["utility"],
                "std_error": row["std_error"],
                "poll_count": row["poll_count"],
                "calculated_at": row["calculated_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            for row in episode_history
        ]

    latest_calculated_at = max(
        item["calculated_at"] for item in ranking_rows
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    episode_ids_for_candidates = _collect_episode_ids(
        normalized_rows=normalized_rows,
        raw_polls=polls,
        episode_metadata_by_id=episode_metadata_by_id,
    )

    finalized_polls = [poll for poll in polls if str(poll.get("finalized_at") or "").strip()]
    running_polls = [poll for poll in polls if not str(poll.get("finalized_at") or "").strip()]

    next_match_candidates: List[Dict[str, Any]] = []
    try:
        next_match_candidates = get_next_match_candidates_from_data(
            episode_ids=episode_ids_for_candidates,
            finalized_polls=finalized_polls,
            running_polls=running_polls,
            rating_rows=rating_rows,
            limit=3,
        )
    except MatchmakingError as e:
        logger.warning("Matchmaking-Kandidaten konnten nicht berechnet werden: %s", e)

    episode_engagement_cards = _build_episode_engagement_cards(
        ranking_rows=ranking,
        votes_per_episode=poll_analytics["votes_per_episode"],
    )

    avg_std_error = sum(row["std_error"] for row in ranking_rows) / len(ranking_rows)
    avg_poll_count = sum(row["poll_count"] for row in ranking_rows) / len(ranking_rows)

    return {
        "has_rankings": True,
        "generated_at": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "latest_calculated_at": latest_calculated_at,
        "ranking": ranking,
        "history_by_episode": history_serialized,
        "episode_ids": sorted(history_by_episode.keys()),
        "metadata_available": metadata_available,
        "metadata_warning": metadata_warning,
        "episode_metadata_by_id": episode_metadata_by_id,
        "open_polls": open_polls,
        "all_polls": poll_analytics["all_polls"],
        "top_exciting_polls": ranked_poll_views["top_exciting_polls"],
        "top_reach_polls": ranked_poll_views["top_reach_polls"],
        "votes_trend": ranked_poll_views["votes_trend"],
        "episode_engagement_cards": episode_engagement_cards,
        "next_match_candidates": next_match_candidates,
        "next_match_candidates_provisional": True,
        "kpis": {
            "ranked_episodes": len(ranking),
            "open_polls": len(open_polls),
            "avg_std_error": avg_std_error,
            "avg_poll_count": avg_poll_count,
            "total_votes": poll_analytics["total_votes"],
            "avg_votes_per_poll": poll_analytics["avg_votes_per_poll"],
            "median_votes_per_poll": poll_analytics["median_votes_per_poll"],
        },
    }


def build_visualization_site(
    ratings_file: Path,
    output_dir: Path,
    polls_file: Optional[Path] = None,
    update_ratings_from_polls: bool = True,
) -> None:
    """
    Baut die statische Visualisierungsseite in output_dir.

    Args:
        ratings_file: Pfad zur ratings.tsv
        output_dir: Zielordner fuer index.html/CSS/JS/JSON
        polls_file: Optionaler Pfad zur polls.tsv (fuer auto-update)
        update_ratings_from_polls: Auto-Update von ratings.tsv vor Site-Build

    Raises:
        VisualizationError: Bei Build-Fehlern
        TSVError: Bei TSV-Ladefehlern
    """
    project_root = Path(__file__).parent.parent
    web_assets_dir = project_root / "web"

    if not web_assets_dir.exists():
        raise VisualizationError(f"Web-Assets-Verzeichnis fehlt: {web_assets_dir}")

    if update_ratings_from_polls:
        if polls_file is None:
            raise VisualizationError("polls_file ist erforderlich fuer Auto-Update")
        update_ratings_from_polls_if_needed(polls_file=polls_file, ratings_file=ratings_file)

    try:
        raw_ratings = load_ratings(ratings_file)
    except TSVError:
        raise

    raw_polls: List[Dict[str, str]] = []
    if polls_file is not None:
        raw_polls = load_polls(polls_file)

    metadata_rows: Optional[List[Dict[str, Any]]] = None
    metadata_warning: Optional[str] = None
    try:
        metadata_rows = fetch_all_episode_metadata()
    except APIError as e:
        metadata_warning = (
            "Episoden-Metadaten konnten nicht geladen werden. "
            "Datenquelle: https://api.dreimetadaten.de/"
        )
        logger.warning("Metadaten-Fallback aktiv: %s", e)

    payload = build_visualization_payload(
        rating_rows=raw_ratings,
        raw_polls=raw_polls,
        metadata_rows=metadata_rows,
        metadata_warning=metadata_warning,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for file_name in ["index.html", "styles.css", "app.js"]:
        src = web_assets_dir / file_name
        dst = output_dir / file_name
        if not src.exists():
            raise VisualizationError(f"Asset fehlt: {src}")
        shutil.copy2(src, dst)

    visualization_json_path = data_dir / "visualization.json"
    with open(visualization_json_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    build_meta_path = output_dir / "build_meta.json"
    with open(build_meta_path, "w", encoding="utf-8") as file:
        json.dump({"has_rankings": payload["has_rankings"]}, file, indent=2)

    logger.info("Visualisierungsdaten geschrieben: %s", visualization_json_path)

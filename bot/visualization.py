"""
Erstellung einer statischen Visualisierung fuer GitHub Pages.

Dieses Modul transformiert ratings.tsv in ein JSON-Format fuer das Frontend
und kopiert statische Assets in einen Build-Ordner.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from bot.bradley_terry import BradleyTerryError, filter_and_parse_polls, run_rating_update_from_polls
from bot.logger import get_logger
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
        matches = int(row["matches"])
        calculated_at = _parse_utc_timestamp(row["calculated_at"])
    except KeyError as e:
        raise VisualizationError(f"Fehlendes Feld in Rating-Zeile: {e}") from e
    except ValueError as e:
        raise VisualizationError(f"Ungueltiger Zahlenwert in Rating-Zeile: {e}") from e

    return {
        "episode_id": episode_id,
        "utility": utility,
        "std_error": std_error,
        "matches": matches,
        "calculated_at": calculated_at,
    }


def build_visualization_payload(rating_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Erzeugt das Frontend-JSON aus rohen TSV-Rating-Zeilen.

    Returns:
        Dict mit Ranking (aktueller Stand), Historie und Metainformationen.
    """
    normalized_rows = [_normalize_rating_row(row) for row in rating_rows]

    if not normalized_rows:
        return {
            "has_rankings": False,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latest_calculated_at": None,
            "ranking": [],
            "history_by_episode": {},
            "episode_ids": [],
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
                "matches": row["matches"],
                "calculated_at": row["calculated_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )

    history_serialized: Dict[str, List[Dict[str, Any]]] = {}
    for episode_id, episode_history in history_by_episode.items():
        history_serialized[str(episode_id)] = [
            {
                "episode_id": row["episode_id"],
                "utility": row["utility"],
                "std_error": row["std_error"],
                "matches": row["matches"],
                "calculated_at": row["calculated_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            for row in episode_history
        ]

    latest_calculated_at = max(
        item["calculated_at"] for item in ranking_rows
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "has_rankings": True,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "latest_calculated_at": latest_calculated_at,
        "ranking": ranking,
        "history_by_episode": history_serialized,
        "episode_ids": sorted(history_by_episode.keys()),
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

    payload = build_visualization_payload(raw_ratings)

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

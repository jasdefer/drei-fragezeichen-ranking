"""
Tests für Bradley-Terry Rating-Modul

Testet die I/O-freie Funktion compute_ratings_from_polls() ohne Dateisystem-Zugriffe.
Fokus auf Ordnungen und Invarianten, keine exakten Zahlenwerte.
"""

from datetime import datetime, timezone

import pytest
import numpy as np

from bot.bradley_terry import compute_ratings_from_polls, BradleyTerryError


def test_happy_path_simple_preference():
    """
    Test: Einfache Präferenzordnung mit klarem Gewinner.
    
    Episode 1 gewinnt gegen alle anderen → höchste utility
    Erwartung: utility > 0, mean ≈ 1.0, Episode 1 hat höchste utility
    """
    # Synthetische Polls: Episode 1 schlägt 2 und 3
    polls = [
        {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 70, 'votes_b': 30},
        {'episode_a_id': 1, 'episode_b_id': 3, 'votes_a': 80, 'votes_b': 20},
        {'episode_a_id': 2, 'episode_b_id': 3, 'votes_a': 60, 'votes_b': 40},
    ]
    
    calculated_at = datetime.now(timezone.utc)
    rating_rows = compute_ratings_from_polls(polls, calculated_at)
    
    # Parse utilities
    utilities = {row['episode_id']: row['utility'] for row in rating_rows}
    
    # Assertions: Ordnungen und Invarianten
    assert len(utilities) == 3, "Alle 3 Episoden sollten gerankt werden"
    
    # Alle utilities > 0
    for ep_id, util in utilities.items():
        assert util > 0, f"Episode {ep_id}: utility sollte > 0 sein"
    
    # Mean ≈ 1.0 (Normierung)
    mean_utility = np.mean(list(utilities.values()))
    assert abs(mean_utility - 1.0) < 0.01, f"Mean utility sollte ≈ 1.0 sein, ist {mean_utility}"
    
    # Episode 1 sollte höchste utility haben (stärkste Episode)
    assert utilities[1] > utilities[2], "Episode 1 sollte stärker als Episode 2 sein"
    assert utilities[1] > utilities[3], "Episode 1 sollte stärker als Episode 3 sein"
    
    # Episode 2 sollte stärker als Episode 3 sein (2 schlägt 3)
    assert utilities[2] > utilities[3], "Episode 2 sollte stärker als Episode 3 sein"


def test_connectivity_episode_1_present():
    """
    Test: Episode 1 ist verbunden → Modell funktioniert.
    """
    polls = [
        {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 50, 'votes_b': 50},
        {'episode_a_id': 2, 'episode_b_id': 3, 'votes_a': 50, 'votes_b': 50},
    ]
    
    calculated_at = datetime.now(timezone.utc)
    # Sollte nicht fehlschlagen
    rating_rows = compute_ratings_from_polls(polls, calculated_at)
    
    # Prüfe dass Daten zurückgegeben wurden
    assert len(rating_rows) > 0, "Rating-Rows sollten zurückgegeben werden"
    assert len(rating_rows) == 3, "Alle 3 verbundenen Episoden sollten gerankt sein"


def test_connectivity_episode_1_missing():
    """
    Test: Episode 1 fehlt → Exception.
    """
    polls = [
        {'episode_a_id': 2, 'episode_b_id': 3, 'votes_a': 60, 'votes_b': 40},
        {'episode_a_id': 3, 'episode_b_id': 4, 'votes_a': 50, 'votes_b': 50},
    ]
    
    calculated_at = datetime.now(timezone.utc)
    
    # Sollte Exception werfen, da Episode 1 fehlt
    with pytest.raises(BradleyTerryError, match="Episode 1 ist nicht im Vergleichsgraph"):
        compute_ratings_from_polls(polls, calculated_at)


def test_disconnected_episodes():
    """
    Test: Nicht mit Episode 1 verbundene Episoden werden nicht gerankt.
    """
    # Episode 1-2 verbunden, aber 3-4 isoliert
    polls = [
        {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 60, 'votes_b': 40},
        {'episode_a_id': 3, 'episode_b_id': 4, 'votes_a': 50, 'votes_b': 50},
    ]
    
    calculated_at = datetime.now(timezone.utc)
    rating_rows = compute_ratings_from_polls(polls, calculated_at)
    
    # Parse episode IDs
    episode_ids = {row['episode_id'] for row in rating_rows}
    
    # Nur Episoden 1 und 2 sollten gerankt sein
    assert episode_ids == {1, 2}, f"Nur Episoden 1,2 sollten gerankt sein, gefunden: {episode_ids}"


def test_stability_finite_values():
    """
    Test: Utilities enthalten nur finite Werte (keine NaN, Inf).
    """
    # Normale Polls
    polls = [
        {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 100, 'votes_b': 50},
        {'episode_a_id': 2, 'episode_b_id': 3, 'votes_a': 75, 'votes_b': 25},
        {'episode_a_id': 1, 'episode_b_id': 3, 'votes_a': 90, 'votes_b': 10},
    ]
    
    calculated_at = datetime.now(timezone.utc)
    rating_rows = compute_ratings_from_polls(polls, calculated_at)
    
    # Parse und prüfe utilities
    for row in rating_rows:
        utility = row['utility']
        
        # Prüfe auf finite Werte
        assert np.isfinite(utility), f"Utility sollte finite sein, ist {utility}"
        assert not np.isnan(utility), f"Utility sollte nicht NaN sein"
        assert not np.isinf(utility), f"Utility sollte nicht Inf sein"


def test_empty_polls_list():
    """
    Test: Leere Poll-Liste → keine Exception, nur Warnung.
    """
    polls = []
    
    calculated_at = datetime.now(timezone.utc)
    # Sollte nicht fehlschlagen, nur loggen
    rating_rows = compute_ratings_from_polls(polls, calculated_at)
    
    # Leere Liste zurückgegeben
    assert rating_rows == [], "Leere Poll-Liste sollte leere Rating-Liste ergeben"


def test_mean_utility_invariant():
    """
    Test: Mean utility ist immer ≈ 1.0 (Normierung).
    """
    # Verschiedene Szenarien
    test_cases = [
        # Gleichmäßige Verteilung
        [
            {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 50, 'votes_b': 50},
            {'episode_a_id': 2, 'episode_b_id': 3, 'votes_a': 50, 'votes_b': 50},
            {'episode_a_id': 1, 'episode_b_id': 3, 'votes_a': 50, 'votes_b': 50},
        ],
        # Starke Dominanz
        [
            {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 90, 'votes_b': 10},
            {'episode_a_id': 1, 'episode_b_id': 3, 'votes_a': 95, 'votes_b': 5},
            {'episode_a_id': 2, 'episode_b_id': 3, 'votes_a': 70, 'votes_b': 30},
        ],
    ]
    
    calculated_at = datetime.now(timezone.utc)
    
    for polls in test_cases:
        rating_rows = compute_ratings_from_polls(polls, calculated_at)
        utilities = [row['utility'] for row in rating_rows]
        
        mean_utility = np.mean(utilities)
        assert abs(mean_utility - 1.0) < 0.01, f"Mean utility sollte ≈ 1.0 sein, ist {mean_utility}"


def test_timezone_aware_required():
    """
    Test: calculated_at muss timezone-aware UTC sein.
    """
    polls = [
        {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 50, 'votes_b': 50},
    ]
    
    # Naive datetime (kein timezone)
    naive_dt = datetime.now()
    
    # Sollte Exception werfen
    with pytest.raises(BradleyTerryError, match="timezone-aware"):
        compute_ratings_from_polls(polls, naive_dt)


def test_timezone_must_be_utc():
    """
    Test: calculated_at muss spezifisch UTC sein, nicht eine andere Zeitzone.
    """
    from datetime import timedelta
    
    polls = [
        {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 50, 'votes_b': 50},
    ]
    
    # Timezone-aware, aber nicht UTC (z.B. UTC+1)
    non_utc_dt = datetime.now(timezone(timedelta(hours=1)))
    
    # Sollte Exception werfen
    with pytest.raises(BradleyTerryError, match="UTC timezone verwenden"):
        compute_ratings_from_polls(polls, non_utc_dt)

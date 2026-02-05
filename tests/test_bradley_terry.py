"""
Tests für Bradley-Terry Rating-Modul

Testet die I/O-freie Funktion run_rating_update_from_polls() ohne Dateisystem-Zugriffe.
Fokus auf Ordnungen und Invarianten, keine exakten Zahlenwerte.
"""

import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest
import numpy as np

from bot.bradley_terry import run_rating_update_from_polls, BradleyTerryError


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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
        ratings_path = Path(f.name)
    
    try:
        calculated_at = datetime.now(timezone.utc)
        run_rating_update_from_polls(polls, ratings_path, calculated_at)
        
        # Lese Ergebnis
        with open(ratings_path, 'r') as f:
            lines = f.readlines()
        
        # Parse utilities
        utilities = {}
        for line in lines[1:]:  # Skip header
            parts = line.strip().split('\t')
            ep_id = int(parts[0])
            utility = float(parts[1])
            utilities[ep_id] = utility
        
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
        
    finally:
        ratings_path.unlink(missing_ok=True)


def test_connectivity_episode_1_present():
    """
    Test: Episode 1 ist verbunden → Modell funktioniert.
    """
    polls = [
        {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 50, 'votes_b': 50},
        {'episode_a_id': 2, 'episode_b_id': 3, 'votes_a': 50, 'votes_b': 50},
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
        ratings_path = Path(f.name)
    
    try:
        calculated_at = datetime.now(timezone.utc)
        # Sollte nicht fehlschlagen
        run_rating_update_from_polls(polls, ratings_path, calculated_at)
        
        # Prüfe dass Datei geschrieben wurde
        assert ratings_path.exists()
        with open(ratings_path, 'r') as f:
            lines = f.readlines()
        assert len(lines) > 1, "Mindestens Header + Daten sollten geschrieben sein"
        
    finally:
        ratings_path.unlink(missing_ok=True)


def test_connectivity_episode_1_missing():
    """
    Test: Episode 1 fehlt im Graph → Exception.
    """
    # Polls ohne Episode 1
    polls = [
        {'episode_a_id': 2, 'episode_b_id': 3, 'votes_a': 60, 'votes_b': 40},
        {'episode_a_id': 3, 'episode_b_id': 4, 'votes_a': 50, 'votes_b': 50},
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
        ratings_path = Path(f.name)
    
    try:
        calculated_at = datetime.now(timezone.utc)
        
        # Sollte Exception werfen
        with pytest.raises(BradleyTerryError, match="Episode 1 ist nicht im Vergleichsgraph"):
            run_rating_update_from_polls(polls, ratings_path, calculated_at)
        
    finally:
        ratings_path.unlink(missing_ok=True)


def test_connectivity_disconnected_episodes():
    """
    Test: Episoden nicht mit Episode 1 verbunden werden nicht gerankt.
    """
    # Episode 1-2 verbunden, aber 3-4 isoliert
    polls = [
        {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 60, 'votes_b': 40},
        {'episode_a_id': 3, 'episode_b_id': 4, 'votes_a': 50, 'votes_b': 50},
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
        ratings_path = Path(f.name)
    
    try:
        calculated_at = datetime.now(timezone.utc)
        run_rating_update_from_polls(polls, ratings_path, calculated_at)
        
        # Lese Ergebnis
        with open(ratings_path, 'r') as f:
            lines = f.readlines()
        
        # Parse episode IDs
        episode_ids = []
        for line in lines[1:]:  # Skip header
            parts = line.strip().split('\t')
            episode_ids.append(int(parts[0]))
        
        # Nur Episoden 1 und 2 sollten gerankt sein
        assert set(episode_ids) == {1, 2}, f"Nur Episoden 1,2 sollten gerankt sein, gefunden: {episode_ids}"
        
    finally:
        ratings_path.unlink(missing_ok=True)


def test_stability_finite_values():
    """
    Test: Theta und utilities enthalten nur finite Werte (keine NaN, Inf).
    """
    # Normale Polls
    polls = [
        {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 100, 'votes_b': 50},
        {'episode_a_id': 2, 'episode_b_id': 3, 'votes_a': 75, 'votes_b': 25},
        {'episode_a_id': 1, 'episode_b_id': 3, 'votes_a': 90, 'votes_b': 10},
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
        ratings_path = Path(f.name)
    
    try:
        calculated_at = datetime.now(timezone.utc)
        run_rating_update_from_polls(polls, ratings_path, calculated_at)
        
        # Lese Ergebnis
        with open(ratings_path, 'r') as f:
            lines = f.readlines()
        
        # Parse und prüfe utilities
        for line in lines[1:]:  # Skip header
            parts = line.strip().split('\t')
            utility = float(parts[1])
            
            # Prüfe auf finite Werte
            assert np.isfinite(utility), f"Utility sollte finite sein, ist {utility}"
            assert not np.isnan(utility), f"Utility sollte nicht NaN sein"
            assert not np.isinf(utility), f"Utility sollte nicht Inf sein"
        
    finally:
        ratings_path.unlink(missing_ok=True)


def test_empty_polls_list():
    """
    Test: Leere Poll-Liste → keine Exception, nur Warnung.
    """
    polls = []
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
        ratings_path = Path(f.name)
    
    try:
        calculated_at = datetime.now(timezone.utc)
        # Sollte nicht fehlschlagen, nur loggen
        run_rating_update_from_polls(polls, ratings_path, calculated_at)
        
        # Datei sollte nicht existieren (nichts geschrieben)
        # oder leer sein (nur Header möglicherweise)
        
    finally:
        ratings_path.unlink(missing_ok=True)


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
            {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 95, 'votes_b': 5},
            {'episode_a_id': 1, 'episode_b_id': 3, 'votes_a': 90, 'votes_b': 10},
            {'episode_a_id': 2, 'episode_b_id': 3, 'votes_a': 80, 'votes_b': 20},
        ],
    ]
    
    for polls in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            ratings_path = Path(f.name)
        
        try:
            calculated_at = datetime.now(timezone.utc)
            run_rating_update_from_polls(polls, ratings_path, calculated_at)
            
            # Lese utilities
            with open(ratings_path, 'r') as f:
                lines = f.readlines()
            
            utilities = []
            for line in lines[1:]:  # Skip header
                parts = line.strip().split('\t')
                utilities.append(float(parts[1]))
            
            # Mean sollte ≈ 1.0 sein
            mean_utility = np.mean(utilities)
            assert abs(mean_utility - 1.0) < 0.01, f"Mean utility sollte ≈ 1.0 sein, ist {mean_utility}"
            
        finally:
            ratings_path.unlink(missing_ok=True)

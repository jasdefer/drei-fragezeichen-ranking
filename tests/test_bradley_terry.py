"""
Tests für das Bradley-Terry Modul

Diese Tests validieren die Funktionalität der Bradley-Terry-Rating-Berechnung.
"""

import unittest
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
import csv

# Füge das bot-Modul zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.bradley_terry import (
    parse_datetime_utc,
    load_finalized_polls,
    build_connectivity_graph,
    find_connected_component,
    filter_polls_by_episodes,
    count_matches_per_episode,
    normalize_utilities,
    run_rating_update,
    BradleyTerryError
)

import numpy as np


class TestParseDatetimeUTC(unittest.TestCase):
    """Tests für parse_datetime_utc"""
    
    def test_parse_iso_with_z(self):
        """Test: ISO-8601 mit Z suffix"""
        dt = parse_datetime_utc("2024-01-15T10:30:00Z")
        self.assertEqual(dt.year, 2024)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 15)
        self.assertEqual(dt.hour, 10)
        self.assertEqual(dt.tzinfo, timezone.utc)
    
    def test_parse_iso_with_offset(self):
        """Test: ISO-8601 mit +00:00 suffix"""
        dt = parse_datetime_utc("2024-01-15T10:30:00+00:00")
        self.assertEqual(dt.tzinfo, timezone.utc)
    
    def test_parse_invalid_raises_error(self):
        """Test: Ungültiges Format wirft Exception"""
        with self.assertRaises(BradleyTerryError):
            parse_datetime_utc("not-a-date")
    
    def test_parse_empty_raises_error(self):
        """Test: Leerer String wirft Exception"""
        with self.assertRaises(BradleyTerryError):
            parse_datetime_utc("")


class TestLoadFinalizedPolls(unittest.TestCase):
    """Tests für load_finalized_polls"""
    
    def setUp(self):
        """Setup: Temporäres Verzeichnis für Test-Dateien"""
        self.temp_dir = tempfile.mkdtemp()
        self.polls_path = Path(self.temp_dir) / "polls.tsv"
    
    def create_polls_tsv(self, rows):
        """Hilfsfunktion zum Erstellen einer Test-polls.tsv"""
        with open(self.polls_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['poll_id', 'reddit_post_id', 'created_at', 'closes_at',
                           'episode_a_id', 'episode_b_id', 'votes_a', 'votes_b', 'finalized_at'])
            writer.writerows(rows)
    
    def test_load_valid_polls(self):
        """Test: Lade gültige finalisierte Polls"""
        now = datetime.now(timezone.utc)
        past = (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        self.create_polls_tsv([
            ['1', 'abc', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '1', '2', '10', '5', past]
        ])
        
        polls = load_finalized_polls(self.polls_path, now)
        
        self.assertEqual(len(polls), 1)
        self.assertEqual(polls[0]['episode_a_id'], 1)
        self.assertEqual(polls[0]['episode_b_id'], 2)
        self.assertEqual(polls[0]['votes_a'], 10)
        self.assertEqual(polls[0]['votes_b'], 5)
    
    def test_filter_by_calculated_at(self):
        """Test: Nur Polls bis calculated_at werden geladen"""
        now = datetime.now(timezone.utc)
        past = (now - timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
        future = (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        self.create_polls_tsv([
            ['1', 'abc', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '1', '2', '10', '5', past],
            ['2', 'def', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '2', '3', '8', '7', future]
        ])
        
        polls = load_finalized_polls(self.polls_path, now)
        
        # Nur der Poll aus der Vergangenheit sollte geladen werden
        self.assertEqual(len(polls), 1)
        self.assertEqual(polls[0]['poll_id'], '1')
    
    def test_ignore_zero_votes(self):
        """Test: Polls mit 0 Stimmen werden ignoriert"""
        now = datetime.now(timezone.utc)
        past = (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        self.create_polls_tsv([
            ['1', 'abc', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '1', '2', '0', '0', past],
            ['2', 'def', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '2', '3', '10', '5', past]
        ])
        
        polls = load_finalized_polls(self.polls_path, now)
        
        # Nur Poll mit Stimmen sollte geladen werden
        self.assertEqual(len(polls), 1)
        self.assertEqual(polls[0]['poll_id'], '2')
    
    def test_ignore_non_finalized(self):
        """Test: Polls ohne finalized_at werden ignoriert"""
        now = datetime.now(timezone.utc)
        past = (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        self.create_polls_tsv([
            ['1', 'abc', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '1', '2', '10', '5', ''],
            ['2', 'def', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '2', '3', '8', '7', past]
        ])
        
        polls = load_finalized_polls(self.polls_path, now)
        
        # Nur finalisierter Poll sollte geladen werden
        self.assertEqual(len(polls), 1)
        self.assertEqual(polls[0]['poll_id'], '2')
    
    def test_missing_columns_raises_error(self):
        """Test: Fehlende Spalten werfen Exception"""
        with open(self.polls_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['poll_id', 'episode_a_id'])  # Fehlende Spalten
        
        now = datetime.now(timezone.utc)
        with self.assertRaises(BradleyTerryError):
            load_finalized_polls(self.polls_path, now)


class TestConnectivityGraph(unittest.TestCase):
    """Tests für Graph-Funktionen"""
    
    def test_build_connectivity_graph(self):
        """Test: Baue Konnektivitätsgraph"""
        polls = [
            {'episode_a_id': 1, 'episode_b_id': 2, 'votes_a': 10, 'votes_b': 5},
            {'episode_a_id': 2, 'episode_b_id': 3, 'votes_a': 8, 'votes_b': 7},
            {'episode_a_id': 5, 'episode_b_id': 6, 'votes_a': 6, 'votes_b': 4}
        ]
        
        graph = build_connectivity_graph(polls)
        
        self.assertIn(2, graph[1])
        self.assertIn(1, graph[2])
        self.assertIn(3, graph[2])
        self.assertIn(6, graph[5])
        self.assertEqual(len(graph), 5)  # 1,2,3,5,6
    
    def test_find_connected_component(self):
        """Test: Finde Zusammenhangskomponente"""
        graph = {
            1: {2},
            2: {1, 3},
            3: {2},
            5: {6},
            6: {5}
        }
        
        component = find_connected_component(graph, start_node=1)
        
        self.assertEqual(component, {1, 2, 3})
    
    def test_find_connected_component_single_node(self):
        """Test: Einzelner Knoten"""
        graph = {1: set(), 2: {3}, 3: {2}}
        
        component = find_connected_component(graph, start_node=1)
        
        self.assertEqual(component, {1})
    
    def test_find_connected_component_missing_node(self):
        """Test: Fehlender Knoten gibt leere Menge"""
        graph = {1: {2}, 2: {1}}
        
        component = find_connected_component(graph, start_node=99)
        
        self.assertEqual(component, set())


class TestFilterPollsByEpisodes(unittest.TestCase):
    """Tests für filter_polls_by_episodes"""
    
    def test_filter_polls(self):
        """Test: Filtere Polls nach gültigen Episoden"""
        polls = [
            {'episode_a_id': 1, 'episode_b_id': 2},
            {'episode_a_id': 2, 'episode_b_id': 3},
            {'episode_a_id': 5, 'episode_b_id': 6}
        ]
        valid_episodes = {1, 2, 3}
        
        filtered = filter_polls_by_episodes(polls, valid_episodes)
        
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]['episode_a_id'], 1)
        self.assertEqual(filtered[1]['episode_a_id'], 2)


class TestCountMatchesPerEpisode(unittest.TestCase):
    """Tests für count_matches_per_episode"""
    
    def test_count_matches(self):
        """Test: Zähle Matches pro Episode"""
        polls = [
            {'episode_a_id': 1, 'episode_b_id': 2},
            {'episode_a_id': 1, 'episode_b_id': 3},
            {'episode_a_id': 2, 'episode_b_id': 3}
        ]
        episode_ids = [1, 2, 3]
        
        counts = count_matches_per_episode(polls, episode_ids)
        
        self.assertEqual(counts[1], 2)
        self.assertEqual(counts[2], 2)
        self.assertEqual(counts[3], 2)


class TestNormalizeUtilities(unittest.TestCase):
    """Tests für normalize_utilities"""
    
    def test_normalize_utilities(self):
        """Test: Normiere Utilities auf mean = 1.0"""
        theta = np.array([0.5, 0.0, -0.5])
        
        utilities = normalize_utilities(theta)
        
        # Mean sollte 1.0 sein
        self.assertAlmostEqual(np.mean(utilities), 1.0, places=6)
        
        # Relative Ordnung sollte erhalten bleiben
        self.assertGreater(utilities[0], utilities[1])
        self.assertGreater(utilities[1], utilities[2])


class TestRunRatingUpdate(unittest.TestCase):
    """Integration-Tests für run_rating_update"""
    
    def setUp(self):
        """Setup: Temporäres Verzeichnis für Test-Dateien"""
        self.temp_dir = tempfile.mkdtemp()
        self.polls_path = Path(self.temp_dir) / "polls.tsv"
        self.ratings_path = Path(self.temp_dir) / "ratings.tsv"
    
    def create_polls_tsv(self, rows):
        """Hilfsfunktion zum Erstellen einer Test-polls.tsv"""
        with open(self.polls_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['poll_id', 'reddit_post_id', 'created_at', 'closes_at',
                           'episode_a_id', 'episode_b_id', 'votes_a', 'votes_b', 'finalized_at'])
            writer.writerows(rows)
    
    def test_run_rating_update_basic(self):
        """Test: Basis-Workflow funktioniert"""
        now = datetime.now(timezone.utc)
        past = (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Erstelle einfache Test-Daten
        # Episode 1 schlägt Episode 2, Episode 2 schlägt Episode 3
        self.create_polls_tsv([
            ['1', 'abc', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '1', '2', '20', '10', past],
            ['2', 'def', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '2', '3', '15', '10', past],
            ['3', 'ghi', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '1', '3', '25', '5', past]
        ])
        
        # Führe Update durch
        run_rating_update(self.polls_path, self.ratings_path, calculated_at=now)
        
        # Prüfe dass ratings.tsv erstellt wurde
        self.assertTrue(self.ratings_path.exists())
        
        # Lade und prüfe Ergebnisse
        with open(self.ratings_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            ratings = list(reader)
        
        # 3 Episoden sollten gerankt sein
        self.assertEqual(len(ratings), 3)
        
        # Episode 1 sollte die höchste Utility haben
        utilities = {int(r['episode_id']): float(r['utility']) for r in ratings}
        self.assertGreater(utilities[1], utilities[2])
        self.assertGreater(utilities[2], utilities[3])
        
        # Mean sollte ungefähr 1.0 sein
        mean_utility = np.mean(list(utilities.values()))
        self.assertAlmostEqual(mean_utility, 1.0, places=5)
    
    def test_run_rating_update_drops_disconnected(self):
        """Test: Nicht mit Episode 1 verbundene Episoden werden gedroppt"""
        now = datetime.now(timezone.utc)
        past = (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Episode 1-2 verbunden, Episode 5-6 isoliert
        self.create_polls_tsv([
            ['1', 'abc', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '1', '2', '20', '10', past],
            ['2', 'def', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '5', '6', '15', '10', past]
        ])
        
        # Führe Update durch
        run_rating_update(self.polls_path, self.ratings_path, calculated_at=now)
        
        # Prüfe Ergebnisse
        with open(self.ratings_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            ratings = list(reader)
        
        # Nur Episode 1 und 2 sollten gerankt sein
        episode_ids = {int(r['episode_id']) for r in ratings}
        self.assertEqual(episode_ids, {1, 2})
    
    def test_run_rating_update_no_episode_1_raises_error(self):
        """Test: Fehlende Episode 1 wirft Exception"""
        now = datetime.now(timezone.utc)
        past = (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Nur Episode 5-6, Episode 1 fehlt
        self.create_polls_tsv([
            ['1', 'abc', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '5', '6', '20', '10', past]
        ])
        
        # Sollte Exception werfen
        with self.assertRaises(BradleyTerryError) as cm:
            run_rating_update(self.polls_path, self.ratings_path, calculated_at=now)
        
        self.assertIn("Episode 1", str(cm.exception))
    
    def test_run_rating_update_append_mode(self):
        """Test: Append-Modus - neue Berechnung wird angehängt"""
        now = datetime.now(timezone.utc)
        past1 = (now - timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
        past2 = (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Erste Berechnung
        self.create_polls_tsv([
            ['1', 'abc', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '1', '2', '20', '10', past1]
        ])
        
        run_rating_update(self.polls_path, self.ratings_path, calculated_at=now - timedelta(days=1))
        
        # Zweite Berechnung mit zusätzlichen Daten
        self.create_polls_tsv([
            ['1', 'abc', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '1', '2', '20', '10', past1],
            ['2', 'def', '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z', '2', '3', '15', '10', past2]
        ])
        
        run_rating_update(self.polls_path, self.ratings_path, calculated_at=now)
        
        # Prüfe dass beide Berechnungen in der Datei sind
        with open(self.ratings_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            ratings = list(reader)
        
        # Erste Berechnung: 2 Episoden, Zweite: 3 Episoden = 5 Zeilen
        self.assertEqual(len(ratings), 5)


if __name__ == '__main__':
    unittest.main()

"""
Tests für das Dreimetadaten API-Modul

Diese Tests validieren die Funktionalität des API-Wrappers gegen die echte
Dreimetadaten API.
"""

import unittest
import sys
from pathlib import Path

# Füge das bot-Modul zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.dreimetadaten_api import (
    run_query,
    fetch_all_episodes,
    fetch_episode_metadata,
    APIError,
    APITimeoutError,
    APIResponseError
)


class TestDreimetadatenAPI(unittest.TestCase):
    """Test-Suite für das Dreimetadaten API-Modul"""
    
    def test_fetch_all_episodes_count(self):
        """
        Test: fetch_all_episodes() sollte mindestens 200 Episoden zurückgeben
        """
        episodes = fetch_all_episodes()
        
        # Prüfe, dass eine Liste zurückgegeben wird
        self.assertIsInstance(episodes, list, "fetch_all_episodes sollte eine Liste zurückgeben")
        
        # Prüfe, dass mindestens 200 Episoden vorhanden sind
        self.assertGreaterEqual(
            len(episodes), 
            200, 
            f"Es sollten mindestens 200 Episoden vorhanden sein, aber es wurden nur {len(episodes)} gefunden"
        )
    
    def test_fetch_all_episodes_contains_1_to_200(self):
        """
        Test: fetch_all_episodes() sollte alle Nummern von 1 bis 200 enthalten
        """
        episodes = fetch_all_episodes()
        
        # Extrahiere alle Nummern
        nummern = {ep['nummer'] for ep in episodes}
        
        # Prüfe, dass alle Nummern von 1 bis 200 vorhanden sind
        expected_nummern = set(range(1, 201))
        missing_nummern = expected_nummern - nummern
        
        self.assertEqual(
            len(missing_nummern),
            0,
            f"Folgende Episoden-Nummern fehlen: {sorted(missing_nummern)}"
        )
    
    def test_fetch_all_episodes_structure(self):
        """
        Test: Jede Episode sollte ein 'nummer' Feld haben
        """
        episodes = fetch_all_episodes()
        
        # Prüfe die ersten 10 Episoden
        for episode in episodes[:10]:
            self.assertIsInstance(episode, dict, "Jede Episode sollte ein Dictionary sein")
            self.assertIn('nummer', episode, "Jede Episode sollte ein 'nummer' Feld haben")
            self.assertIsInstance(episode['nummer'], int, "'nummer' sollte eine Ganzzahl sein")
    
    def test_fetch_episode_149_title(self):
        """
        Test: Episode 149 sollte den Titel "Der namenlose Gegner" haben
        """
        episode = fetch_episode_metadata(149)
        
        # Prüfe, dass Episode gefunden wurde
        self.assertIsNotNone(episode, "Episode 149 sollte gefunden werden")
        
        # Prüfe den Titel
        self.assertIn('titel', episode, "Episode sollte ein 'titel' Feld haben")
        self.assertEqual(
            episode['titel'],
            "Der namenlose Gegner",
            f"Episode 149 sollte den Titel 'Der namenlose Gegner' haben, aber hat '{episode['titel']}'"
        )
    
    def test_fetch_episode_149_metadata_complete(self):
        """
        Test: Episode 149 sollte alle Metadaten-Felder ausgefüllt haben
        """
        episode = fetch_episode_metadata(149)
        
        # Prüfe, dass Episode gefunden wurde
        self.assertIsNotNone(episode, "Episode 149 sollte gefunden werden")
        
        # Erwartete Felder
        required_fields = ['nummer', 'titel', 'beschreibung', 'urlCoverApple']
        
        for field in required_fields:
            # Prüfe, dass Feld vorhanden ist
            self.assertIn(field, episode, f"Episode sollte ein '{field}' Feld haben")
            
            # Prüfe, dass Feld nicht leer ist
            value = episode[field]
            self.assertIsNotNone(value, f"Feld '{field}' sollte nicht None sein")
            
            # Für String-Felder: nicht leer
            if field in ['titel', 'beschreibung', 'urlCoverApple']:
                self.assertIsInstance(value, str, f"Feld '{field}' sollte ein String sein")
                self.assertTrue(
                    len(value.strip()) > 0,
                    f"Feld '{field}' sollte nicht leer sein"
                )
            
            # Für nummer: sollte 149 sein
            if field == 'nummer':
                self.assertEqual(value, 149, f"Feld 'nummer' sollte 149 sein")
    
    def test_fetch_episode_metadata_returns_dict(self):
        """
        Test: fetch_episode_metadata() sollte ein Dictionary zurückgeben
        """
        episode = fetch_episode_metadata(1)
        
        self.assertIsNotNone(episode, "Episode 1 sollte gefunden werden")
        self.assertIsInstance(episode, dict, "fetch_episode_metadata sollte ein Dictionary zurückgeben")
    
    def test_fetch_episode_metadata_nonexistent(self):
        """
        Test: fetch_episode_metadata() sollte None für nicht existierende Episoden zurückgeben
        """
        # Versuche eine sehr hohe Nummer, die wahrscheinlich nicht existiert
        episode = fetch_episode_metadata(99999)
        
        self.assertIsNone(
            episode, 
            "fetch_episode_metadata sollte None für nicht existierende Episoden zurückgeben"
        )
    
    def test_run_query_returns_list(self):
        """
        Test: run_query() sollte eine Liste für SELECT-Queries mit _shape=array zurückgeben
        """
        query = "SELECT s.nummer FROM serie s LIMIT 5"
        result = run_query(query)
        
        self.assertIsInstance(result, list, "run_query sollte eine Liste zurückgeben")
        self.assertGreater(len(result), 0, "Ergebnis sollte nicht leer sein")
    
    def test_exceptions_exist(self):
        """
        Test: Prüfe, dass alle Exception-Klassen definiert sind
        """
        # Prüfe, dass Exceptions existieren
        self.assertTrue(issubclass(APIError, Exception))
        self.assertTrue(issubclass(APITimeoutError, APIError))
        self.assertTrue(issubclass(APIResponseError, APIError))


if __name__ == '__main__':
    unittest.main()

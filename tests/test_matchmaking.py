"""Tests fuer Matchmaking-Logik."""

import unittest

from bot.matchmaking import MatchmakingError, select_next_match_from_data


class TestMatchmaking(unittest.TestCase):
    """Tests fuer Seed-Phase und Normalmodus."""

    def test_seed_starts_with_1_vs_2(self):
        pair = select_next_match_from_data(
            episode_ids=list(range(1, 17)),
            finalized_polls=[],
            running_polls=[],
            rating_rows=[],
            epsilon=0.0,
        )
        self.assertEqual(pair, (1, 2))

    def test_seed_skips_running_pair(self):
        pair = select_next_match_from_data(
            episode_ids=list(range(1, 17)),
            finalized_polls=[],
            running_polls=[{'episode_a_id': 1, 'episode_b_id': 2}],
            rating_rows=[],
            epsilon=0.0,
        )
        self.assertEqual(pair, (2, 3))

    def test_seed_progress_after_completed_pairs(self):
        finalized = [
            {'episode_a_id': 1, 'episode_b_id': 2},
            {'episode_a_id': 2, 'episode_b_id': 3},
        ]
        pair = select_next_match_from_data(
            episode_ids=list(range(1, 17)),
            finalized_polls=finalized,
            running_polls=[],
            rating_rows=[],
            epsilon=0.0,
        )
        self.assertEqual(pair, (3, 4))

    def test_normal_mode_uses_frontier_after_seed(self):
        seed_pairs = [
            {'episode_a_id': 1, 'episode_b_id': 2},
            {'episode_a_id': 2, 'episode_b_id': 3},
            {'episode_a_id': 3, 'episode_b_id': 4},
            {'episode_a_id': 4, 'episode_b_id': 5},
            {'episode_a_id': 5, 'episode_b_id': 6},
            {'episode_a_id': 6, 'episode_b_id': 7},
            {'episode_a_id': 7, 'episode_b_id': 8},
            {'episode_a_id': 8, 'episode_b_id': 1},
        ]

        rating_rows = [
            {'episode_id': i, 'utility': 1.0 + (i * 0.01), 'std_error': 0.1, 'matches': 2, 'calculated_at': '2026-02-01T00:00:00Z'}
            for i in range(1, 9)
        ]

        pair = select_next_match_from_data(
            episode_ids=list(range(1, 17)),
            finalized_polls=seed_pairs,
            running_polls=[],
            rating_rows=rating_rows,
            epsilon=0.0,
            random_seed=7,
        )

        self.assertTrue(9 in pair or 10 in pair or 11 in pair or 12 in pair)

    def test_raises_when_all_active_episodes_blocked(self):
        seed_pairs = [
            {'episode_a_id': 1, 'episode_b_id': 2},
            {'episode_a_id': 2, 'episode_b_id': 3},
            {'episode_a_id': 3, 'episode_b_id': 4},
            {'episode_a_id': 4, 'episode_b_id': 5},
            {'episode_a_id': 5, 'episode_b_id': 6},
            {'episode_a_id': 6, 'episode_b_id': 7},
            {'episode_a_id': 7, 'episode_b_id': 8},
            {'episode_a_id': 8, 'episode_b_id': 1},
        ]

        with self.assertRaises(MatchmakingError):
            select_next_match_from_data(
                episode_ids=list(range(1, 17)),
                finalized_polls=seed_pairs,
                running_polls=[
                    {'episode_a_id': 1, 'episode_b_id': 2},
                    {'episode_a_id': 3, 'episode_b_id': 4},
                    {'episode_a_id': 5, 'episode_b_id': 6},
                    {'episode_a_id': 7, 'episode_b_id': 8},
                    {'episode_a_id': 9, 'episode_b_id': 10},
                    {'episode_a_id': 11, 'episode_b_id': 12},
                ],
                rating_rows=[],
                epsilon=0.0,
            )


if __name__ == '__main__':
    unittest.main()

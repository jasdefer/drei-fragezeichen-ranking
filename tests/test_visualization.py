"""Tests fuer den Visualisierungs-Datenaufbau."""

import unittest

from bot.visualization import build_visualization_payload


class TestVisualizationPayload(unittest.TestCase):
    """Tests fuer build_visualization_payload()."""

    def test_empty_payload(self):
        payload = build_visualization_payload([])

        self.assertFalse(payload["has_rankings"])
        self.assertEqual(payload["site_variant"], "prod")
        self.assertIsNone(payload["environment_banner"])
        self.assertIsNone(payload["latest_calculated_at"])
        self.assertEqual(payload["ranking"], [])
        self.assertEqual(payload["history_by_episode"], {})
        self.assertEqual(payload["episode_ids"], [])

    def test_test_variant_contains_environment_banner(self):
        payload = build_visualization_payload([], site_variant="test")

        self.assertEqual(payload["site_variant"], "test")
        self.assertIsNotNone(payload["environment_banner"])
        self.assertEqual(payload["environment_banner"]["title"], "TESTINSTANZ")

    def test_latest_snapshot_and_history(self):
        rows = [
            {
                "episode_id": "1",
                "utility": "1.100000",
                "std_error": "0.120000",
                "poll_count": "8",
                "calculated_at": "2026-02-10T10:00:00Z",
            },
            {
                "episode_id": "2",
                "utility": "0.900000",
                "std_error": "0.150000",
                "poll_count": "8",
                "calculated_at": "2026-02-10T10:00:00Z",
            },
            {
                "episode_id": "1",
                "utility": "1.050000",
                "std_error": "0.090000",
                "poll_count": "10",
                "calculated_at": "2026-02-12T10:00:00Z",
            },
            {
                "episode_id": "2",
                "utility": "0.950000",
                "std_error": "0.140000",
                "poll_count": "10",
                "calculated_at": "2026-02-12T10:00:00Z",
            },
            {
                "episode_id": "3",
                "utility": "1.200000",
                "std_error": "0.300000",
                "poll_count": "2",
                "calculated_at": "2026-02-11T10:00:00Z",
            },
        ]

        payload = build_visualization_payload(rows)

        self.assertTrue(payload["has_rankings"])
        self.assertEqual(payload["latest_calculated_at"], "2026-02-12T10:00:00Z")

        # Ranking basiert auf jeweils neuestem Eintrag pro Episode.
        ranking_episode_ids = [entry["episode_id"] for entry in payload["ranking"]]
        self.assertEqual(ranking_episode_ids, [3, 1, 2])

        # Episode 1 Historie ist chronologisch sortiert.
        episode_1_history = payload["history_by_episode"]["1"]
        self.assertEqual(
            [entry["calculated_at"] for entry in episode_1_history],
            ["2026-02-10T10:00:00Z", "2026-02-12T10:00:00Z"],
        )

        self.assertEqual(payload["episode_ids"], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()

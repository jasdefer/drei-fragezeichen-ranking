#!/usr/bin/env python3
"""
Bradley-Terry-Modell: Beispielimplementierung mit Dummy-Daten

Dieses Skript demonstriert die Anwendung des Bradley-Terry-Modells zur
Auswertung von paarweisen Vergleichen am Beispiel von fiktiven Umfragen
über "Die drei ???"-Folgen.

Es zeigt:
1. Datengenerierung (simulierte Umfragen)
2. Datenaufbereitung (Konvertierung zu paarweisen Vergleichen)
3. Modellschätzung mit choix
4. Ergebnisdarstellung und Interpretation

Verwendung:
    python examples/bradley_terry_example.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Prüfe ob choix installiert ist
try:
    import choix
    import numpy as np
except ImportError as e:
    print("❌ Fehler: Erforderliche Bibliotheken nicht installiert")
    print("\nBitte installieren Sie:")
    print("  pip install choix numpy")
    print(f"\nFehlerdetails: {e}")
    sys.exit(1)


def generate_dummy_polls(n_episodes=10, n_polls=30, seed=42):
    """
    Generiert Dummy-Umfragen mit realistischen Eigenschaften.
    
    Simuliert einen Datensatz mit:
    - Verschiedenen "wahren" Stärken für jede Folge
    - Stochastischen Abstimmungsergebnissen basierend auf diesen Stärken
    - Verschiedenen Stimmenzahlen pro Umfrage
    
    Args:
        n_episodes: Anzahl der simulierten Folgen
        n_polls: Anzahl der simulierten Umfragen
        seed: Random Seed für Reproduzierbarkeit
        
    Returns:
        Liste von Poll-Dictionaries
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Generiere "wahre" latente Stärken für jede Folge
    # Diese sind normalverteilt um 0 (im Log-Space)
    true_strengths = np.random.randn(n_episodes)
    true_utilities = np.exp(true_strengths)
    
    print(f"📊 Generiere {n_polls} Dummy-Polls für {n_episodes} Folgen")
    print(f"   Wahre Stärken (normiert): {true_utilities / np.mean(true_utilities)}")
    print()
    
    polls = []
    poll_id = 1
    base_date = datetime(2024, 1, 1)
    
    for i in range(n_polls):
        # Wähle zwei zufällige Folgen
        ep_a, ep_b = random.sample(range(n_episodes), 2)
        
        # Berechne wahre Win-Probability nach Bradley-Terry
        p_a_wins = true_utilities[ep_a] / (true_utilities[ep_a] + true_utilities[ep_b])
        
        # Simuliere Anzahl der Stimmen (variiert zwischen 40 und 120)
        total_votes = random.randint(40, 120)
        
        # Simuliere Abstimmungsergebnis (binomial verteilt)
        votes_a = np.random.binomial(total_votes, p_a_wins)
        votes_b = total_votes - votes_a
        
        # Erstelle Poll-Eintrag
        created_at = base_date + timedelta(days=i*7)
        closes_at = created_at + timedelta(days=7)
        finalized_at = closes_at + timedelta(hours=2)
        
        polls.append({
            'poll_id': poll_id,
            'reddit_post_id': f'dummy_{poll_id:03d}',
            'created_at': created_at.isoformat() + 'Z',
            'closes_at': closes_at.isoformat() + 'Z',
            'episode_a_id': ep_a,
            'episode_b_id': ep_b,
            'votes_a': votes_a,
            'votes_b': votes_b,
            'finalized_at': finalized_at.isoformat() + 'Z'
        })
        poll_id += 1
    
    return polls, true_utilities


def polls_to_comparisons(polls):
    """
    Konvertiert aggregierte Poll-Daten zu paarweisen Vergleichen.
    
    Disaggregierung: Jede Stimme wird als ein einzelner paarweiser Vergleich
    behandelt. Bei 65 Stimmen für A vs 35 für B entstehen:
    - 65 Vergleiche (A > B)
    - 35 Vergleiche (B > A)
    
    Args:
        polls: Liste von Poll-Dictionaries
        
    Returns:
        comparisons: Liste von (winner_id, loser_id) Tupeln
        episode_ids: Sortierte Liste aller vorkommenden Episode-IDs
    """
    comparisons = []
    episode_ids = set()
    
    for poll in polls:
        ep_a = poll['episode_a_id']
        ep_b = poll['episode_b_id']
        votes_a = poll['votes_a']
        votes_b = poll['votes_b']
        
        episode_ids.update([ep_a, ep_b])
        
        # Disaggregierung: jede Stimme als ein Vergleich
        for _ in range(votes_a):
            comparisons.append((ep_a, ep_b))
        for _ in range(votes_b):
            comparisons.append((ep_b, ep_a))
    
    return comparisons, sorted(episode_ids)


def compute_bradley_terry_ratings(comparisons, episode_ids, alpha=0.01):
    """
    Berechnet Bradley-Terry-Stärken mit L2-Regularisierung.
    
    Args:
        comparisons: Liste von (winner_id, loser_id) Tupeln
        episode_ids: Sortierte Liste aller Episode-IDs
        alpha: Regularisierungsparameter (Standard: 0.01)
        
    Returns:
        Dictionary mit:
        - episode_ids: Liste der Folgen-IDs
        - utilities: Normierte Stärken (Durchschnitt = 1.0)
        - log_strengths: Rohe Log-Stärken (für Debugging)
        - match_counts: Anzahl Vergleiche pro Folge
    """
    n_items = len(episode_ids)
    
    # Mappe episode_ids zu Indizes 0, 1, 2, ...
    id_to_idx = {ep_id: idx for idx, ep_id in enumerate(episode_ids)}
    indexed_comparisons = [
        (id_to_idx[winner], id_to_idx[loser]) 
        for winner, loser in comparisons
    ]
    
    print(f"🔬 Berechne Bradley-Terry-Modell:")
    print(f"   Folgen: {n_items}")
    print(f"   Vergleiche: {len(comparisons)}")
    print(f"   Regularisierung (alpha): {alpha}")
    
    # Bradley-Terry mit L2-Regularisierung (ILSR-Algorithmus)
    log_strengths = choix.ilsr_pairwise(
        n_items=n_items,
        data=indexed_comparisons,
        alpha=alpha,
        max_iter=10000
    )
    
    # Transformation: Log → Utility (normiert auf Durchschnitt)
    utilities = np.exp(log_strengths)
    normalized_utilities = utilities / np.mean(utilities)
    
    # Zähle Matches pro Folge
    match_counts = {ep_id: 0 for ep_id in episode_ids}
    for winner, loser in comparisons:
        match_counts[winner] += 1
        match_counts[loser] += 1
    
    return {
        'episode_ids': episode_ids,
        'utilities': normalized_utilities,
        'log_strengths': log_strengths,
        'match_counts': [match_counts[ep_id] for ep_id in episode_ids]
    }


def print_results(results, true_utilities=None):
    """
    Gibt die Ergebnisse übersichtlich aus.
    
    Args:
        results: Ergebnisse von compute_bradley_terry_ratings()
        true_utilities: Optionale wahre Stärken (für Validierung)
    """
    print("\n" + "="*70)
    print("📊 BRADLEY-TERRY ERGEBNISSE")
    print("="*70)
    
    # Erstelle Ranking
    ranking = sorted(
        zip(results['episode_ids'], results['utilities'], results['match_counts']),
        key=lambda x: x[1],
        reverse=True
    )
    
    print(f"\n{'Rang':<6} {'Episode':<10} {'Utility':<12} {'Matches':<10}")
    print("-" * 70)
    
    for rank, (ep_id, utility, matches) in enumerate(ranking, start=1):
        print(f"{rank:<6} {ep_id:<10} {utility:>10.4f}   {matches:<10}")
    
    # Wenn wahre Stärken verfügbar, vergleiche
    if true_utilities is not None:
        print("\n" + "="*70)
        print("🔍 VERGLEICH MIT WAHREN STÄRKEN")
        print("="*70)
        
        # Normiere wahre Stärken
        true_norm = true_utilities / np.mean(true_utilities)
        
        print(f"\n{'Episode':<10} {'Geschätzt':<12} {'Wahr':<12} {'Differenz':<12}")
        print("-" * 70)
        
        for ep_id, est_util in zip(results['episode_ids'], results['utilities']):
            true_util = true_norm[ep_id]
            diff = est_util - true_util
            print(f"{ep_id:<10} {est_util:>10.4f}   {true_util:>10.4f}   {diff:>+10.4f}")
        
        # Berechne Korrelation
        correlation = np.corrcoef(results['utilities'], true_norm[results['episode_ids']])[0, 1]
        print(f"\n✓ Korrelation (geschätzt vs. wahr): {correlation:.4f}")
        print("  (Perfekt wäre 1.0, > 0.9 ist sehr gut)")
    
    print("\n" + "="*70)


def demonstrate_parameter_effects():
    """
    Demonstriert den Einfluss verschiedener Parameter auf das Ergebnis.
    """
    print("\n" + "="*70)
    print("🔬 PARAMETER-SENSITIVITÄT")
    print("="*70)
    
    # Generiere kleine Testdaten
    polls, true_utilities = generate_dummy_polls(n_episodes=5, n_polls=10, seed=42)
    comparisons, episode_ids = polls_to_comparisons(polls)
    
    # Teste verschiedene alpha-Werte
    alphas = [0.0, 0.001, 0.01, 0.1, 1.0]
    
    print("\nEinfluss der Regularisierung (alpha):")
    print(f"{'alpha':<10} {'Utility Episode 0':<20} {'Utility Episode 4':<20}")
    print("-" * 70)
    
    for alpha in alphas:
        results = compute_bradley_terry_ratings(comparisons, episode_ids, alpha=alpha)
        util_0 = results['utilities'][0]
        util_4 = results['utilities'][4]
        print(f"{alpha:<10.3f} {util_0:>18.4f}   {util_4:>18.4f}")
    
    print("\n💡 Beobachtung:")
    print("  - alpha = 0: Keine Regularisierung (MLE)")
    print("  - Höhere alpha-Werte 'ziehen' Stärken zur Mitte (utility ≈ 1.0)")
    print("  - Für dieses Projekt empfohlen: alpha = 0.01 (schwache Regularisierung)")


def save_example_output():
    """
    Erstellt eine Beispiel-ratings.tsv Datei mit Dummy-Daten.
    """
    output_dir = Path(__file__).parent.parent / 'examples'
    output_file = output_dir / 'example_ratings.tsv'
    
    polls, true_utilities = generate_dummy_polls(n_episodes=10, n_polls=30)
    comparisons, episode_ids = polls_to_comparisons(polls)
    results = compute_bradley_terry_ratings(comparisons, episode_ids)
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    with open(output_file, 'w') as f:
        # Header
        f.write("episode_id\tutility\tmatches\tcalculated_at\n")
        
        # Datenzeilen
        for ep_id, utility, matches in zip(
            results['episode_ids'],
            results['utilities'],
            results['match_counts']
        ):
            f.write(f"{ep_id}\t{utility:.6f}\t{matches}\t{timestamp}\n")
    
    print(f"\n✓ Beispiel-Ausgabe gespeichert: {output_file}")


def main():
    """Hauptfunktion: Demonstriert den kompletten Workflow."""
    print("\n" + "="*70)
    print("BRADLEY-TERRY-MODELL: BEISPIELIMPLEMENTIERUNG")
    print("="*70)
    print("\nDieses Skript demonstriert die Verwendung des Bradley-Terry-Modells")
    print("zur Auswertung von paarweisen Vergleichen mit simulierten Daten.")
    print("="*70)
    
    # 1. Generiere Dummy-Daten
    print("\n[1/5] Generiere Dummy-Umfragen...")
    polls, true_utilities = generate_dummy_polls(n_episodes=10, n_polls=30)
    print(f"✓ {len(polls)} Umfragen generiert")
    
    # 2. Konvertiere zu paarweisen Vergleichen
    print("\n[2/5] Konvertiere zu paarweisen Vergleichen...")
    comparisons, episode_ids = polls_to_comparisons(polls)
    print(f"✓ {len(comparisons)} paarweise Vergleiche erstellt")
    
    # 3. Berechne Bradley-Terry-Ratings
    print("\n[3/5] Berechne Bradley-Terry-Ratings...")
    results = compute_bradley_terry_ratings(comparisons, episode_ids, alpha=0.01)
    print("✓ Berechnung abgeschlossen")
    
    # 4. Zeige Ergebnisse
    print("\n[4/5] Ergebnisse:")
    print_results(results, true_utilities)
    
    # 5. Parameter-Sensitivität
    print("\n[5/5] Parameter-Analyse:")
    demonstrate_parameter_effects()
    
    # Optional: Speichere Beispiel-Ausgabe
    save_example_output()
    
    print("\n" + "="*70)
    print("✓ BEISPIEL ABGESCHLOSSEN")
    print("="*70)
    print("\nWeitere Informationen:")
    print("  - Dokumentation: docs/bradley_terry_model.md")
    print("  - choix Library: https://choix.lum.li/")
    print("="*70)


if __name__ == '__main__':
    main()

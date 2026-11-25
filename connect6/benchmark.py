"""Head-to-head AI matches: ``python -m connect6.benchmark --games 20``.

Each pairing plays an even number of games, alternating who moves first, and reports wins,
losses, draws and average thinking time per stone.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .ai import GreedyAI, MinimaxAI
from .board import P1, P2, Game


def play(ai1, ai2, max_stones: int = 361) -> tuple:
    game, times = Game(), {P1: [], P2: []}
    players = {P1: ai1, P2: ai2}
    while not game.over and len(game.history) < max_stones:
        t = time.perf_counter()
        col = players[game.to_move].choose(game)
        times[game.to_move].append(time.perf_counter() - t)
        game.play(col)
    return game.winner, times, len(game.history)


def match(make_a, make_b, games: int) -> dict:
    res = {"a_wins": 0, "b_wins": 0, "draws": 0, "stones": [], "a_ms": [], "b_ms": []}
    for g in range(games):
        a, b = make_a(g), make_b(g)
        first, second = (a, b) if g % 2 == 0 else (b, a)
        winner, times, n = play(first, second)
        a_side = P1 if g % 2 == 0 else P2
        if winner is None:
            res["draws"] += 1
        elif winner == a_side:
            res["a_wins"] += 1
        else:
            res["b_wins"] += 1
        res["stones"].append(n)
        res["a_ms"] += [1000 * t for t in times[a_side]]
        res["b_ms"] += [1000 * t for t in times[P2 if a_side == P1 else P1]]
    avg = lambda xs: round(sum(xs) / max(len(xs), 1), 1)
    return {"a": make_a(0).name, "b": make_b(0).name, "games": games, "a_wins": res["a_wins"],
            "b_wins": res["b_wins"], "draws": res["draws"], "avg_stones_per_game": avg(res["stones"]),
            "a_ms_per_stone": avg(res["a_ms"]), "b_ms_per_stone": avg(res["b_ms"])}


def main(argv=None) -> list:
    ap = argparse.ArgumentParser(description="Benchmark the Connect-6 AIs against each other.")
    ap.add_argument("--games", type=int, default=20)
    ap.add_argument("--out", default="results/benchmark.json")
    args = ap.parse_args(argv)
    pairings = [
        (lambda s: MinimaxAI(depth=1, seed=s), lambda s: GreedyAI(seed=1000 + s)),
        (lambda s: MinimaxAI(depth=2, seed=s), lambda s: GreedyAI(seed=1000 + s)),
        (lambda s: MinimaxAI(depth=2, seed=s), lambda s: MinimaxAI(depth=1, seed=1000 + s)),
    ]
    results = []
    for a, b in pairings:
        r = match(a, b, args.games)
        print(json.dumps(r), flush=True)
        results.append(r)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


if __name__ == "__main__":
    main()

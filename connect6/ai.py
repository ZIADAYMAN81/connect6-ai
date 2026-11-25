"""Computer players.

* ``GreedyAI`` places each stone where the static evaluation is highest (the coursework's original
  ``pick_best_move``), used as a baseline.
* ``MinimaxAI`` searches whole *turns* (pairs of stones) with alpha-beta pruning. Before searching it
  takes any immediate win and blocks any immediate threat, and it only considers the most promising
  columns (move ordering + beam), which keeps a 19 x 19 board fast enough for real-time play.
"""
from __future__ import annotations

import math
import random
from itertools import combinations_with_replacement
from typing import List, Optional, Tuple

import numpy as np

from .board import DIRECTIONS, EMPTY, WIN_LENGTH, Board, Game, opponent

WEIGHTS = {6: 1_000_000, 5: 5_000, 4: 400, 3: 40, 2: 5, 1: 1}


def _windows(grid: np.ndarray) -> np.ndarray:
    """All length-6 lines on the board as an (n, 6) array (rows, columns and both diagonals)."""
    k, rows, cols = WIN_LENGTH, grid.shape[0], grid.shape[1]
    out = [np.lib.stride_tricks.sliding_window_view(grid, k, axis=1).reshape(-1, k),
           np.lib.stride_tricks.sliding_window_view(grid, k, axis=0).reshape(-1, k)]
    for g in (grid, np.fliplr(grid)):
        for off in range(-(rows - k), cols - k + 1):
            d = np.diagonal(g, offset=off)
            if len(d) >= k:
                out.append(np.lib.stride_tricks.sliding_window_view(d, k))
    return np.concatenate(out)


def evaluate(board: Board, player: int) -> float:
    """Score windows that contain only one player's stones; positive favours ``player``."""
    w = _windows(board.grid)
    mine, theirs = (w == player).sum(1), (w == opponent(player)).sum(1)
    score = 0.0
    for n, weight in WEIGHTS.items():
        score += weight * np.count_nonzero((mine == n) & (theirs == 0))
        score -= 1.2 * weight * np.count_nonzero((theirs == n) & (mine == 0))   # defence slightly prioritised
    centre = board.cols // 2
    score += 2 * np.count_nonzero(board.grid[:, centre] == player)
    return score


class GreedyAI:
    name = "Greedy (one-stone lookahead)"

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def choose(self, game: Game) -> int:
        b, me = game.board, game.to_move
        best, best_cols = -math.inf, []
        for col in b.valid_columns():
            b.drop(col, me)
            s = evaluate(b, me)
            b.undo(col)
            if s > best:
                best, best_cols = s, [col]
            elif s == best:
                best_cols.append(col)
        return self.rng.choice(best_cols)


class MinimaxAI:
    def __init__(self, depth: int = 2, beam: int = 6, seed: Optional[int] = None):
        self.depth, self.beam = depth, beam
        self.rng = random.Random(seed)
        self.name = f"Alpha-beta minimax (depth {depth} turns, beam {beam})"
        self._plan: List[int] = []

    # --- helpers ---------------------------------------------------------------------------
    def _winning_columns(self, b: Board, player: int) -> List[int]:
        wins = []
        for col in b.valid_columns():
            row = b.drop(col, player)
            if b.wins_at(row, col):
                wins.append(col)
            b.undo(col)
        return wins

    def _ordered(self, b: Board, player: int) -> List[int]:
        scored = []
        for col in b.valid_columns():
            b.drop(col, player)
            scored.append((evaluate(b, player), col))
            b.undo(col)
        scored.sort(reverse=True)
        return [c for _, c in scored[: self.beam]]

    def _turn_options(self, b: Board, player: int, stones: int) -> List[Tuple[int, ...]]:
        cols = self._ordered(b, player)
        if stones == 1:
            return [(c,) for c in cols]
        return list(combinations_with_replacement(cols, 2))

    def _apply(self, b: Board, player: int, cols: Tuple[int, ...]) -> Tuple[List[int], bool]:
        played, won = [], False
        for col in cols:
            if b.heights[col] >= b.rows:
                break
            row = b.drop(col, player)
            played.append(col)
            if b.wins_at(row, col):
                won = True
                break
        return played, won

    def _search(self, b: Board, player: int, me: int, depth: int, alpha: float, beta: float) -> float:
        if depth == 0 or b.is_full():
            return evaluate(b, me)
        maximising = player == me
        value = -math.inf if maximising else math.inf
        for option in self._turn_options(b, player, 2):
            played, won = self._apply(b, player, option)
            score = (1e9 if player == me else -1e9) if won else self._search(b, opponent(player), me, depth - 1, alpha, beta)
            for col in reversed(played):
                b.undo(col)
            if maximising:
                value, alpha = max(value, score), max(alpha, score)
            else:
                value, beta = min(value, score), min(beta, score)
            if alpha >= beta:
                break
        return value

    # --- public ----------------------------------------------------------------------------
    def choose(self, game: Game) -> int:
        """Return the next column. A two-stone turn is planned once and played stone by stone."""
        b, me = game.board, game.to_move
        if self._plan and game.stones_left == 1 and b.heights[self._plan[0]] < b.rows:
            return self._plan.pop(0)
        self._plan = []

        wins = self._winning_columns(b, me)
        if wins:
            return wins[0]
        threats = self._winning_columns(b, opponent(me))
        if threats:
            if game.stones_left == 2 and len(threats) > 1:
                self._plan = [threats[1]]
            return threats[0]

        best, best_options = -math.inf, []
        for option in self._turn_options(b, me, game.stones_left):
            played, won = self._apply(b, me, option)
            score = 1e9 if won else self._search(b, opponent(me), me, self.depth - 1, -math.inf, math.inf)
            for col in reversed(played):
                b.undo(col)
            if score > best:
                best, best_options = score, [option]
            elif score == best:
                best_options.append(option)
        option = list(self.rng.choice(best_options))
        self._plan = option[1:]
        return option[0]

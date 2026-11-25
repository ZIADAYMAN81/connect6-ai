"""Board representation and game rules.

Rules (Connect-6 played with gravity, as in Connect Four):
* Stones drop to the lowest empty cell of the chosen column on a 19 x 19 board.
* The first player places **one** stone on the opening turn; after that, each turn is **two** stones.
* Six in a row (horizontally, vertically or diagonally) wins; a full board is a draw.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

EMPTY, P1, P2 = 0, 1, 2
WIN_LENGTH = 6
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


def opponent(player: int) -> int:
    return P2 if player == P1 else P1


@dataclass
class Board:
    rows: int = 19
    cols: int = 19
    grid: np.ndarray = field(default=None)

    def __post_init__(self):
        if self.grid is None:
            self.grid = np.zeros((self.rows, self.cols), dtype=np.int8)
        self.heights = (self.grid != EMPTY).sum(axis=0).astype(int)

    def copy(self) -> "Board":
        b = Board(self.rows, self.cols, self.grid.copy())
        return b

    def valid_columns(self) -> List[int]:
        return [c for c in range(self.cols) if self.heights[c] < self.rows]

    def is_full(self) -> bool:
        return all(h >= self.rows for h in self.heights)

    def drop(self, col: int, player: int) -> int:
        """Place a stone; returns the row index (0 = bottom)."""
        if not 0 <= col < self.cols or self.heights[col] >= self.rows:
            raise ValueError(f"column {col} is not playable")
        row = self.heights[col]
        self.grid[row, col] = player
        self.heights[col] += 1
        return row

    def undo(self, col: int) -> None:
        self.heights[col] -= 1
        self.grid[self.heights[col], col] = EMPTY

    def line_length(self, row: int, col: int, dr: int, dc: int) -> int:
        """Length of the run of the stone at (row, col) along one direction (both ways)."""
        player, n = self.grid[row, col], 1
        for sign in (1, -1):
            r, c = row + sign * dr, col + sign * dc
            while 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r, c] == player:
                n += 1
                r, c = r + sign * dr, c + sign * dc
        return n

    def wins_at(self, row: int, col: int) -> bool:
        """Did the stone just placed at (row, col) complete six in a row? O(1) per move."""
        return self.grid[row, col] != EMPTY and any(
            self.line_length(row, col, dr, dc) >= WIN_LENGTH for dr, dc in DIRECTIONS)

    def has_six(self, player: int) -> bool:
        """Full-board check (used by tests and as a safety net)."""
        g = self.grid == player
        k = WIN_LENGTH
        for dr, dc in DIRECTIONS:
            for r in range(self.rows):
                for c in range(self.cols):
                    rr, cc = r + (k - 1) * dr, c + (k - 1) * dc
                    if 0 <= rr < self.rows and 0 <= cc < self.cols and all(g[r + i * dr, c + i * dc] for i in range(k)):
                        return True
        return False


@dataclass
class Game:
    """Turn order and game state on top of a Board."""

    board: Board = field(default_factory=Board)
    to_move: int = P1
    stones_left: int = 1          # opening turn has a single stone
    winner: Optional[int] = None
    history: List[Tuple[int, int]] = field(default_factory=list)  # (player, column)

    @property
    def over(self) -> bool:
        return self.winner is not None or self.board.is_full()

    def play(self, col: int) -> int:
        if self.over:
            raise RuntimeError("game is over")
        row = self.board.drop(col, self.to_move)
        self.history.append((self.to_move, col))
        if self.board.wins_at(row, col):
            self.winner = self.to_move
            return row
        self.stones_left -= 1
        if self.stones_left == 0:
            self.to_move, self.stones_left = opponent(self.to_move), 2
        return row

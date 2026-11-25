"""Play against the AI: ``python -m connect6.gui --depth 2``.

Click a column to drop a stone (two stones per turn after the opening move).
Press R to restart and Esc to quit.
"""
from __future__ import annotations

import argparse

import pygame

from .ai import MinimaxAI
from .board import P1, P2, Game

CELL, MARGIN, STATUS = 34, 20, 48
BOARD_BG, GRID, P1_COLOUR, P2_COLOUR = (240, 190, 110), (60, 40, 20), (250, 250, 250), (25, 25, 25)
HIGHLIGHT, TEXT = (200, 60, 60), (30, 30, 30)


class App:
    def __init__(self, depth: int, ai_first: bool):
        pygame.init()
        pygame.display.set_caption("Connect-6 vs AI")
        self.game = Game()
        self.cols, self.rows = self.game.board.cols, self.game.board.rows
        self.size = (2 * MARGIN + self.cols * CELL, 2 * MARGIN + self.rows * CELL + STATUS)
        self.screen = pygame.display.set_mode(self.size)
        self.font = pygame.font.SysFont("segoeui,arial", 20)
        self.depth, self.ai_first = depth, ai_first
        self.reset()

    def reset(self):
        self.game = Game()
        self.ai = MinimaxAI(depth=self.depth)
        self.human = P2 if self.ai_first else P1
        self.last = None

    def cell_centre(self, row: int, col: int):
        x = MARGIN + col * CELL + CELL // 2
        y = MARGIN + (self.rows - 1 - row) * CELL + CELL // 2   # row 0 is the bottom
        return x, y

    def column_at(self, x: int):
        col = (x - MARGIN) // CELL
        return col if 0 <= col < self.cols else None

    def draw(self, hover_col=None):
        s = self.screen
        s.fill((245, 245, 245))
        pygame.draw.rect(s, BOARD_BG, (MARGIN, MARGIN, self.cols * CELL, self.rows * CELL))
        for c in range(self.cols + 1):
            x = MARGIN + c * CELL
            pygame.draw.line(s, GRID, (x, MARGIN), (x, MARGIN + self.rows * CELL))
        for r in range(self.rows + 1):
            y = MARGIN + r * CELL
            pygame.draw.line(s, GRID, (MARGIN, y), (MARGIN + self.cols * CELL, y))
        if hover_col is not None and not self.game.over:
            pygame.draw.rect(s, HIGHLIGHT, (MARGIN + hover_col * CELL, MARGIN, CELL, self.rows * CELL), 2)
        g = self.game.board.grid
        for r in range(self.rows):
            for c in range(self.cols):
                if g[r, c]:
                    pygame.draw.circle(s, P1_COLOUR if g[r, c] == P1 else P2_COLOUR, self.cell_centre(r, c), CELL // 2 - 3)
                    pygame.draw.circle(s, GRID, self.cell_centre(r, c), CELL // 2 - 3, 1)
        if self.last:
            pygame.draw.circle(s, HIGHLIGHT, self.cell_centre(*self.last), 5)
        s.blit(self.font.render(self.status(), True, TEXT), (MARGIN, self.size[1] - STATUS + 10))
        pygame.display.flip()

    def status(self) -> str:
        g = self.game
        if g.winner:
            return ("You win!" if g.winner == self.human else "The AI wins.") + "  Press R to play again."
        if g.over:
            return "Draw.  Press R to play again."
        who = "Your turn" if g.to_move == self.human else "AI is thinking..."
        return f"{who}  ({g.stones_left} stone{'s' if g.stones_left > 1 else ''} to place)"

    def play(self, col: int):
        row = self.game.play(col)
        self.last = (row, col)

    def run(self):
        clock, hover = pygame.time.Clock(), None
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    pygame.quit()
                    return
                if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                    self.reset()
                if e.type == pygame.MOUSEMOTION:
                    hover = self.column_at(e.pos[0])
                if (e.type == pygame.MOUSEBUTTONDOWN and not self.game.over and self.game.to_move == self.human):
                    col = self.column_at(e.pos[0])
                    if col is not None and col in self.game.board.valid_columns():
                        self.play(col)
            self.draw(hover)
            if not self.game.over and self.game.to_move != self.human:
                self.play(self.ai.choose(self.game))
            clock.tick(30)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Play Connect-6 against an alpha-beta AI.")
    ap.add_argument("--depth", type=int, default=2, help="search depth in turns (1 = fast, 2 = stronger)")
    ap.add_argument("--ai-first", action="store_true", help="let the AI make the opening move")
    args = ap.parse_args(argv)
    App(args.depth, args.ai_first).run()


if __name__ == "__main__":
    main()

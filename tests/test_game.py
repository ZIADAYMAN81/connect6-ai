import pytest

from connect6.ai import GreedyAI, MinimaxAI, evaluate
from connect6.board import P1, P2, Board, Game


def test_gravity_and_undo():
    b = Board(rows=6, cols=7)
    assert b.drop(3, P1) == 0 and b.drop(3, P2) == 1
    b.undo(3)
    assert b.heights[3] == 1 and b.grid[1, 3] == 0


def test_full_column_rejected():
    b = Board(rows=2, cols=3)
    b.drop(0, P1); b.drop(0, P2)
    with pytest.raises(ValueError):
        b.drop(0, P1)
    assert b.valid_columns() == [1, 2]


@pytest.mark.parametrize("cells", [
    [(0, c) for c in range(6)],                      # horizontal
    [(r, 0) for r in range(6)],                      # vertical
    [(i, i) for i in range(6)],                      # rising diagonal
    [(i, 6 - i) for i in range(6)],                  # falling diagonal
])
def test_six_in_a_row_in_every_direction(cells):
    b = Board()
    for r, c in cells:
        b.grid[r, c] = P1
    assert all(b.wins_at(r, c) for r, c in cells)
    assert b.has_six(P1) and not b.has_six(P2)


def test_five_is_not_a_win():
    b = Board()
    for c in range(5):
        b.grid[0, c] = P1
    assert not b.wins_at(0, 2) and not b.has_six(P1)


def test_turn_order_is_one_then_two_stones():
    g = Game()
    order = []
    for col in [0, 1, 2, 3, 4, 5, 6]:
        order.append(g.to_move)
        g.play(col)
    assert order == [P1, P2, P2, P1, P1, P2, P2]


def test_game_stops_at_a_win():
    g = Game(board=Board(rows=19, cols=19))
    p2_cols = iter([10, 12, 14, 16, 18, 11, 13, 15, 17])   # scattered, so P2 never makes six
    for col in range(6):                     # P1 builds the bottom row
        while g.to_move != P1:
            g.play(next(p2_cols))
        g.play(col)
    assert g.winner == P1
    with pytest.raises(RuntimeError):
        g.play(10)


def test_ai_takes_an_immediate_win_and_blocks_a_threat():
    g = Game()
    g.board.grid[0, 0:5] = P2            # P2 has five on the bottom row
    g.board.heights[0:5] = 1
    g.to_move, g.stones_left = P2, 2
    assert MinimaxAI(depth=1, seed=0).choose(g) == 5

    g.to_move = P1                        # now P1 must block column 5
    assert MinimaxAI(depth=1, seed=0).choose(g) == 5


def test_evaluation_prefers_longer_lines():
    a, b = Board(), Board()
    a.grid[0, 0:4] = P1
    b.grid[0, 0:2] = P1
    assert evaluate(a, P1) > evaluate(b, P1)


def test_ais_play_only_legal_moves():
    g = Game(board=Board(rows=8, cols=8))
    players = {P1: MinimaxAI(depth=1, seed=1), P2: GreedyAI(seed=2)}
    while not g.over:
        col = players[g.to_move].choose(g)
        assert col in g.board.valid_columns()
        g.play(col)

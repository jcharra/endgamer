import chess.pgn
import chess
import random


def random_krb_kr():
    board = chess.Board(None)

    pieces = [
        (chess.WHITE, chess.KING),
        (chess.WHITE, chess.ROOK),
        (chess.WHITE, chess.BISHOP),
        (chess.BLACK, chess.KING),
        (chess.BLACK, chess.ROOK),
    ]

    squares = random.sample(range(64), len(pieces))

    for sq, (color, piece) in zip(squares, pieces):
        board.set_piece_at(sq, chess.Piece(piece, color))

    board.turn = random.choice([True, False])
    if board.is_valid():
        return board

    return None


GAMES = []


def get_random_endgame():
    global GAMES
    if len(GAMES) == 0:
        pgn = open("data/endgames.pgn")

        while True:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break
            GAMES.append(game.headers["FEN"])
    return random.choice(GAMES)
  
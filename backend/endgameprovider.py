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


def _is_valid_position(fen):
    try:
        board = chess.Board(fen)
        pieces = board.piece_map().values()
        only_kings_and_pawns = all(p.piece_type in (chess.KING, chess.PAWN) for p in pieces)
        return only_kings_and_pawns and len(list(pieces)) <= 5 and not board.is_game_over()
    except Exception:
        return False


def get_random_endgame():
    global GAMES
    if len(GAMES) == 0:
        with open("data/endgames.pgn") as pgn:
            while True:
                game = chess.pgn.read_game(pgn)
                if game is None:
                    break
                fen = game.headers["FEN"]
                if _is_valid_position(fen):
                    GAMES.append(fen)
    return random.choice(GAMES)
  
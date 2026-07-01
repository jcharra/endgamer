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


# Curated, pre-filtered position sets produced by filter_endgames.py. Each
# file holds only positions that are a clean win for the side to move,
# bucketed by material (see that script for how the buckets are built).
# The keys here double as the category names used by the frontend's
# category-picking buttons and the /new?category=... API parameter.
CATEGORY_FILES = {
    "pawns_only": "data/pawns_only.fen",
    "3_pieces": "data/3_pieces.fen",
    "4_pieces": "data/4_pieces.fen",
    "5_pieces": "data/5_pieces.fen",
}

# Cache of category name -> list of FENs, populated lazily so each file
# is only read from disk once, no matter how often it is requested.
_CATEGORY_CACHE = {}


def _load_category(category):
    """Return the list of FENs for a single category, reading the
    underlying file from disk the first time the category is requested
    and reusing the cached list afterwards.

    Raises KeyError if the category name is not one of CATEGORY_FILES.
    """
    if category not in _CATEGORY_CACHE:
        with open(CATEGORY_FILES[category]) as endgame_set:
            _CATEGORY_CACHE[category] = [line.strip() for line in endgame_set if line.strip()]
    return _CATEGORY_CACHE[category]


def get_random_endgame(category=None):
    """Return a random winning-position FEN.

    When a category is given, the FEN is drawn only from that
    category's curated set (see CATEGORY_FILES for the valid names).
    Without a category, a FEN is drawn from the combined pool of every
    category.

    Raises KeyError if an unknown category is requested, and IndexError
    if the (possibly filtered) pool of positions to choose from is
    empty.
    """
    if category is not None:
        return random.choice(_load_category(category))

    all_fens = []
    for name in CATEGORY_FILES:
        all_fens.extend(_load_category(name))
    return random.choice(all_fens)
  
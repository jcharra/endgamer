"""One-off preprocessing script that turns the raw Syzygy PGN dump into
curated, winning-only position sets, bucketed by material.

Run it directly (``python filter_endgames.py``) whenever data/endgames.pgn
changes. The resulting *.fen files are what endgameprovider.py serves at
runtime, so the app itself never has to re-parse the huge PGN file or
re-apply the winning-position filter on every startup.
"""

import chess
import chess.pgn

SOURCE_PGN = "data/endgames.pgn"

# Maps each bucket name to the file it is written to. "pawns_only" holds
# every winning position whose non-king material is exclusively pawns,
# regardless of how many pieces are on the board. The numeric buckets
# hold everything else, keyed by total piece count (2 kings + N pieces).
CATEGORY_FILES = {
    "pawns_only": "data/pawns_only.fen",
    3: "data/3_pieces.fen",
    4: "data/4_pieces.fen",
    5: "data/5_pieces.fen",
}


def categorize_position(fen):
    """Work out which curated bucket a position belongs to.

    Returns the bucket key ("pawns_only", 3, 4 or 5) or None if the
    position should be discarded, i.e. it has fewer than 3 or more than
    5 pieces on the board.
    """
    board = chess.Board(fen)
    piece_map = board.piece_map()
    piece_count = len(piece_map)

    if piece_count < 3 or piece_count > 5:
        return None

    non_king_pieces = [piece for piece in piece_map.values() if piece.piece_type != chess.KING]
    only_pawns = all(piece.piece_type == chess.PAWN for piece in non_king_pieces)

    if only_pawns:
        return "pawns_only"

    return piece_count


def filter_and_split(source_path=SOURCE_PGN):
    """Read every game from the raw PGN dump, keep only the positions
    that are a clean win for the side to move, bucket the survivors by
    material, and write each bucket out to its own file.

    Returns a dict mapping bucket name to the number of positions kept,
    which is handy for a quick sanity check after running the script.
    """
    buckets = {category: [] for category in CATEGORY_FILES}

    with open(source_path) as pgn_file:
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break

            # Only keep positions that are a genuine win for the side to
            # move; draws, losses and "cursed" wins (wins that the
            # 50-move rule could turn into a draw) are not suitable for
            # a trainer that expects the player to always be able to win.
            if game.headers.get("WDL") != "Win":
                continue

            fen = game.headers["FEN"]
            category = categorize_position(fen)
            if category is not None:
                buckets[category].append(fen)

    for category, fens in buckets.items():
        output_path = CATEGORY_FILES[category]
        with open(output_path, "w") as out_file:
            out_file.write("\n".join(fens) + "\n")

    return {category: len(fens) for category, fens in buckets.items()}


if __name__ == "__main__":
    result_counts = filter_and_split()
    for category, count in result_counts.items():
        print(f"{category}: {count} winning positions")

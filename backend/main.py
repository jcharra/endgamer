import chess
import urllib.request
import urllib.parse
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

from endgameprovider import get_random_endgame

app = Flask(__name__)
CORS(app)


def query_tablebase(b):
    url = 'https://tablebase.lichess.ovh/standard?' + \
        urllib.parse.urlencode({'fen': b.fen()})
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def get_outcome(fen):
    try:
        tb = query_tablebase(chess.Board(fen))
        wdl = tb.get('wdl')
        dtz = tb.get('dtz')
        val = wdl if wdl is not None else dtz
        if val is None:
            return None
        return 1 if val > 0 else (0 if val == 0 else -1)
    except Exception:
        return None


def position_task(fen, outcome=None):
    if outcome is None:
        outcome = get_outcome(fen)
    if outcome is None:
        return None
    color = 'White' if fen.split()[1] == 'w' else 'Black'
    return f'{color} to {"win" if outcome > 0 else "draw"}'


POSITION_FEN = get_random_endgame()
BOARD = chess.Board(POSITION_FEN)
HUMAN_COLOR = chess.WHITE if POSITION_FEN.split()[1] == 'w' else chess.BLACK
POSITION_TASK = position_task(POSITION_FEN)


@app.route('/new', methods=['GET'])
def new():
    global BOARD, POSITION_FEN, HUMAN_COLOR, POSITION_TASK
    outcome = -1
    for _ in range(10):
        POSITION_FEN = get_random_endgame()
        outcome = get_outcome(POSITION_FEN)
        if outcome is not None and outcome >= 0:
            break
    BOARD = chess.Board(POSITION_FEN)
    HUMAN_COLOR = chess.WHITE if POSITION_FEN.split()[1] == 'w' else chess.BLACK
    POSITION_TASK = position_task(POSITION_FEN, outcome)
    return jsonify({'fen': POSITION_FEN, 'task': POSITION_TASK})


@app.route('/position', methods=['GET'])
def get_position():
    BOARD.set_fen(POSITION_FEN)
    return jsonify({'fen': POSITION_FEN, 'task': POSITION_TASK})


@app.route('/dests', methods=['GET'])
def get_dests():
    dests = {}
    seen = set()
    for move in BOARD.legal_moves:
        from_sq = chess.square_name(move.from_square)
        to_sq = chess.square_name(move.to_square)
        if (from_sq, to_sq) not in seen:
            seen.add((from_sq, to_sq))
            dests.setdefault(from_sq, []).append(to_sq)
    return jsonify({'dests': dests, 'fen': BOARD.fen()})



@app.route('/move', methods=['POST'])
def make_move():
    data = request.get_json()
    uci = data['from'] + data['to'] + data.get('promotion', '')
    move = chess.Move.from_uci(uci)

    if move not in BOARD.legal_moves:
        return jsonify({'error': 'illegal move'}), 400

    best_uci = None
    optimal = True
    try:
        tb = query_tablebase(BOARD)
        moves = tb.get('moves') or []
        if moves:
            best = moves[0]
            best_uci = best.get('uci')
            played = next((m for m in moves if m['uci'] == uci), None)
            if played is not None:
                bd, pd = best.get('dtz'), played.get('dtz')
                if bd is not None and pd is not None:
                    def cat(d): return 1 if d < 0 else (0 if d == 0 else -1)
                    optimal = cat(pd) >= cat(bd)
    except Exception as e:
        print(f'Tablebase query error: {e}')

    if not optimal:
        return jsonify({'fen': BOARD.fen(), 'optimal': False, 'best_move': best_uci})

    BOARD.push(move)

    if not BOARD.is_game_over() and BOARD.turn != HUMAN_COLOR:
        try:
            tb_reply = query_tablebase(BOARD)
            reply_moves = tb_reply.get('moves', [])
            if reply_moves:
                BOARD.push(chess.Move.from_uci(reply_moves[0]['uci']))
        except Exception as e:
            print(f'Black reply error: {e}')

    return jsonify({'fen': BOARD.fen(), 'optimal': True})


app.run(host='0.0.0.0', port=8001)

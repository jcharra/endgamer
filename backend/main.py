import chess
import urllib.request
import urllib.parse
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

POSITION_FEN = '4k3/8/8/8/8/8/3PP3/4K3 w - - 0 1'  # K+P vs K
board = chess.Board(POSITION_FEN)


@app.route('/position', methods=['GET'])
def get_position():
    board.set_fen(POSITION_FEN)
    return jsonify({'fen': POSITION_FEN})


@app.route('/dests', methods=['GET'])
def get_dests():
    dests = {}
    seen = set()
    for move in board.legal_moves:
        from_sq = chess.square_name(move.from_square)
        to_sq = chess.square_name(move.to_square)
        if (from_sq, to_sq) not in seen:
            seen.add((from_sq, to_sq))
            dests.setdefault(from_sq, []).append(to_sq)
    return jsonify({'dests': dests, 'fen': board.fen()})


def query_tablebase(b):
    url = 'https://tablebase.lichess.ovh/standard?' + urllib.parse.urlencode({'fen': b.fen()})
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


@app.route('/move', methods=['POST'])
def make_move():
    data = request.get_json()
    uci = data['from'] + data['to'] + data.get('promotion', '')
    move = chess.Move.from_uci(uci)

    if move not in board.legal_moves:
        return jsonify({'error': 'illegal move'}), 400

    best_uci = None
    optimal = True
    try:
        tb = query_tablebase(board)
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
        return jsonify({'fen': board.fen(), 'optimal': False, 'best_move': best_uci})

    board.push(move)

    if not board.is_game_over() and board.turn == chess.BLACK:
        try:
            tb_reply = query_tablebase(board)
            reply_moves = tb_reply.get('moves', [])
            if reply_moves:
                board.push(chess.Move.from_uci(reply_moves[0]['uci']))
        except Exception as e:
            print(f'Black reply error: {e}')

    return jsonify({'fen': board.fen(), 'optimal': True})


app.run(host='0.0.0.0', port=8000)

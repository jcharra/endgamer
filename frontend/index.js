import { Chessground } from '@lichess-org/chessground';
import '@lichess-org/chessground/assets/chessground.base.css';
import '@lichess-org/chessground/assets/chessground.brown.css';
import '@lichess-org/chessground/assets/chessground.cburnett.css';

async function fetchPosition() {
  const res = await fetch('http://localhost:8000/position');
  const data = await res.json();
  return data.fen;
}

async function fetchDests() {
  const res = await fetch('http://localhost:8000/dests');
  const data = await res.json();
  return { dests: new Map(Object.entries(data.dests)), fen: data.fen };
}

async function sendMove(from, to, promotion = '') {
  const res = await fetch('http://localhost:8000/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ from, to, promotion }),
  });
  return res.json();
}

function askPromotion() {
  return new Promise((resolve) => {
    const dialog = document.getElementById('promotion-dialog');
    dialog.classList.add('visible');
    dialog.addEventListener('click', function handler(e) {
      const btn = e.target.closest('[data-piece]');
      if (!btn) return;
      dialog.classList.remove('visible');
      dialog.removeEventListener('click', handler);
      resolve(btn.dataset.piece);
    });
  });
}

async function onMove(from, to) {
  const piece = ground.state.pieces.get(to);
  const promotion = piece?.role === 'pawn' && to[1] === '8' ? await askPromotion() : '';
  const data = await sendMove(from, to, promotion);
  if (data.error) {
    console.error('illegal move:', data.error);
    return;
  }
  if (!data.optimal) {
    document.getElementById('board').classList.add('dark');
    const best = data.best_move;
    ground.set({
      movable: { color: undefined },
      drawable: {
        autoShapes: best ? [{ orig: best.slice(0, 2), dest: best.slice(2, 4), brush: 'yellow' }] : [],
      },
    });
    return;
  }

  document.getElementById('board').classList.remove('dark');
  const next = await fetchDests();
  ground.set({
    fen: next.fen,
    turnColor: 'white',
    movable: { dests: next.dests, events: { after: onMove } },
    drawable: { autoShapes: [] },
  });
}

const initialFen = await fetchPosition();
const { dests } = await fetchDests();

const ground = Chessground(document.getElementById('board'), {
  fen: initialFen,
  movable: {
    free: false,
    color: 'white',
    dests,
    events: { after: onMove },
  },
});

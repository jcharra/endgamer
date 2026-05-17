import { Chessground } from '@lichess-org/chessground';
import '@lichess-org/chessground/assets/chessground.base.css';
import '@lichess-org/chessground/assets/chessground.brown.css';
import '@lichess-org/chessground/assets/chessground.cburnett.css';

let humanColor = 'white';

function fenColor(fen) {
  return fen.split(' ')[1] === 'w' ? 'white' : 'black';
}

async function fetchPosition() {
  const res = await fetch('http://localhost:8000/position');
  return res.json();
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
  const promoRank = humanColor === 'white' ? '8' : '1';
  const promotion = piece?.role === 'pawn' && to[1] === promoRank ? await askPromotion() : '';
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
    turnColor: humanColor,
    movable: { dests: next.dests, events: { after: onMove } },
    drawable: { autoShapes: [] },
  });
}

async function loadPosition(posData = null) {
  const { fen, task } = posData ?? await fetchPosition();
  document.getElementById('task').textContent = task ?? '';
  humanColor = fenColor(fen);
  const { dests } = await fetchDests();
  document.getElementById('board').classList.remove('dark');
  ground.set({
    fen,
    orientation: humanColor,
    turnColor: humanColor,
    movable: { color: humanColor, free: false, dests, events: { after: onMove } },
    drawable: { autoShapes: [] },
  });
}

document.getElementById('new-btn').addEventListener('click', async () => {
  const res = await fetch('http://localhost:8000/new');
  await loadPosition(await res.json());
});

const { fen: initialFen, task: initialTask } = await fetchPosition();
document.getElementById('task').textContent = initialTask ?? '';
humanColor = fenColor(initialFen);
const { dests } = await fetchDests();

const ground = Chessground(document.getElementById('board'), {
  fen: initialFen,
  orientation: humanColor,
  turnColor: humanColor,
  movable: {
    free: false,
    color: humanColor,
    dests,
    events: { after: onMove },
  },
});

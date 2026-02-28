/* ── Custom cursor ─────────────────────────────────────────────────────── */
const cursor     = document.getElementById('cursor');
const cursorRing = document.getElementById('cursor-ring');
let mx = 0, my = 0, rx = 0, ry = 0;

document.addEventListener('mousemove', e => {
  mx = e.clientX;
  my = e.clientY;
});

function animateCursor() {
  cursor.style.left = mx + 'px';
  cursor.style.top  = my + 'px';
  rx += (mx - rx) * 0.12;
  ry += (my - ry) * 0.12;
  cursorRing.style.left = rx + 'px';
  cursorRing.style.top  = ry + 'px';
  requestAnimationFrame(animateCursor);
}
animateCursor();


/* ── Scroll reveal ─────────────────────────────────────────────────────── */
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      entry.target.style.transitionDelay = (i * 0.06) + 's';
      entry.target.classList.add('visible');
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));


/* ── Terminal squat animation ──────────────────────────────────────────── */
let squats = 0;
let angle  = 160;
let going  = 'down';

const animCount = document.getElementById('anim-count');
const animAngle = document.getElementById('anim-angle');
const animBar   = document.getElementById('anim-bar');
const animStage = document.getElementById('anim-stage');

setInterval(() => {
  going === 'down' ? angle -= 4 : angle += 4;

  if (angle <= 55)  going = 'up';
  if (angle >= 160) {
    going = 'down';
    squats++;
    animCount.textContent = squats;
  }

  animAngle.textContent = angle + '°';

  // Progress bar: 160° = 0%, 55° = 100%
  const pct = Math.round(((160 - angle) / (160 - 55)) * 100);
  animBar.style.width = pct + '%';

  if (angle < 100) {
    animStage.textContent  = 'DOWN';
    animStage.style.color  = 'var(--blue)';
  } else {
    animStage.textContent  = 'UP';
    animStage.style.color  = 'var(--accent)';
  }
}, 80);
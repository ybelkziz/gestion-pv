// ── TOAST ──────────────────────────────────────────────────────
function showToast(msg, type='success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// ── AUTO-DISMISS ALERTS ────────────────────────────────────────
document.querySelectorAll('.alert').forEach(a => {
  setTimeout(() => a.style.opacity === '' && a.remove(), 5000);
});

// ── SIDEBAR OVERLAY CLOSE (mobile) ────────────────────────────
document.addEventListener('click', (e) => {
  const sidebar = document.getElementById('sidebar');
  const toggle  = document.querySelector('.menu-toggle');
  if (sidebar && sidebar.classList.contains('open')) {
    if (!sidebar.contains(e.target) && e.target !== toggle) {
      sidebar.classList.remove('open');
    }
  }
});

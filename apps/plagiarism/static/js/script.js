const toggle = document.getElementById('theme-toggle');
const spans = toggle.querySelectorAll('span');

const currentTheme = localStorage.getItem('theme') || 'dark';
document.body.className = currentTheme + '-mode';
spans.forEach(s => s.classList.toggle('active', s.dataset.mode === currentTheme));

toggle.addEventListener('click', function(e) {
    const span = e.target.closest('span');
    if (!span || !span.dataset.mode) return;

    const mode = span.dataset.mode;
    document.body.className = mode + '-mode';
    localStorage.setItem('theme', mode);
    spans.forEach(s => s.classList.toggle('active', s.dataset.mode === mode));
});

// Logout modal
(function() {
    const logoutBtn = document.getElementById('logout-btn');
    const modal = document.getElementById('logout-modal');
    const cancelBtn = document.getElementById('modal-cancel');

    if (!logoutBtn || !modal || !cancelBtn) return;

    logoutBtn.addEventListener('click', function(e) {
        e.preventDefault();
        modal.style.display = 'flex';
    });

    cancelBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
})();
const toggle = document.getElementById('theme-toggle');

// Check local storage for theme preference
const currentTheme = localStorage.getItem('theme') || 'light';
document.body.className = currentTheme + '-mode';
toggle.checked = currentTheme === 'dark';

// Toggle theme
toggle.addEventListener('change', function() {
    if (this.checked) {
        document.body.className = 'dark-mode';
        localStorage.setItem('theme', 'dark');
    } else {
        document.body.className = 'light-mode';
        localStorage.setItem('theme', 'light');
    }
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
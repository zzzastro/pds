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
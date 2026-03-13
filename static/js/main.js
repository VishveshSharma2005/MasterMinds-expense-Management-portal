function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('mm_theme', theme);

    const toggleButton = document.getElementById('themeToggle');
    if (!toggleButton) {
        return;
    }

    const isDark = theme === 'dark';
    toggleButton.textContent = isDark ? 'Light Mode' : 'Dark Mode';
    toggleButton.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
}

document.addEventListener('click', function (event) {
    if (event.target.matches('.flash-close')) {
        const flash = event.target.closest('.flash');
        if (flash) {
            flash.remove();
        }
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(currentTheme);

    const toggleButton = document.getElementById('themeToggle');
    if (toggleButton) {
        toggleButton.addEventListener('click', function () {
            const activeTheme = document.documentElement.getAttribute('data-theme') || 'light';
            applyTheme(activeTheme === 'dark' ? 'light' : 'dark');
        });
    }

    setTimeout(function () {
        document.querySelectorAll('.flash').forEach(function (flash) {
            flash.style.transition = 'opacity 0.25s ease';
            flash.style.opacity = '0';
            setTimeout(function () {
                flash.remove();
            }, 260);
        });
    }, 5000);
});

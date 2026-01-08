// Theme toggle functionality
function toggleTheme() {
    const root = document.documentElement;
    const icon = document.getElementById('theme-icon');
    const currentTheme = localStorage.getItem('theme');
    
    if (currentTheme === 'dark') {
        root.classList.remove('dark-mode');
        root.classList.add('light-mode');
        localStorage.setItem('theme', 'light');
        icon.textContent = '🌙';
    } else if (currentTheme === 'light') {
        localStorage.removeItem('theme');
        root.classList.remove('light-mode');
        root.classList.remove('dark-mode');
        icon.textContent = '🌓';
    } else {
        root.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
        icon.textContent = '☀️';
    }
    
    // Trigger custom event for charts or other components that need to update
    window.dispatchEvent(new Event('themechange'));
}

// Apply saved theme on page load
(function() {
    const savedTheme = localStorage.getItem('theme');
    const icon = document.getElementById('theme-icon');
    if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark-mode');
        if (icon) icon.textContent = '☀️';
    } else if (savedTheme === 'light') {
        document.documentElement.classList.add('light-mode');
        if (icon) icon.textContent = '🌙';
    } else {
        // Auto mode - check system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (icon) icon.textContent = prefersDark ? '☀️' : '🌙';
    }
})();

// Helper function to check if dark mode is active
function isDarkModeActive() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') return true;
    if (savedTheme === 'light') return false;
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

// Navigation toggle functionality
function toggleNav() {
    const navLinks = document.getElementById('nav-links');
    navLinks.classList.toggle('active');
}

// History sub-menu toggle functionality
function toggleHistoryMenu(event) {
    // Only on mobile (when hamburger menu is visible)
    if (window.innerWidth <= 768) {
        event.preventDefault();
        const historySubnav = document.getElementById('history-subnav');
        const historyToggle = event.currentTarget;
        
        historySubnav.classList.toggle('expanded');
        historyToggle.classList.toggle('collapsed');
    }
    // On desktop, allow normal navigation to /history
}

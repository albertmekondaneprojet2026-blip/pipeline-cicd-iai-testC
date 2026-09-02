document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const toggle = document.getElementById('menuToggle');

    function closeSidebar() {
        sidebar?.classList.remove('open');
        overlay?.classList.remove('active');
    }

    toggle?.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('active');
    });
    overlay?.addEventListener('click', closeSidebar);
    document.querySelectorAll('.sidebar .nav-item').forEach(link => {
        link.addEventListener('click', closeSidebar);
    });
});
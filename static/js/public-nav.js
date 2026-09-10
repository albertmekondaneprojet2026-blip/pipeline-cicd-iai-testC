document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('mobileNavToggle');
    const panel = document.getElementById('mobileNavPanel');

    toggle?.addEventListener('click', () => {
        panel.classList.toggle('open');
    });
});
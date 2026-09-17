document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.row-actions-toggle').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const dropdown = btn.nextElementSibling;
            const isOpen = dropdown.classList.contains('open');
            document.querySelectorAll('.row-actions-dropdown.open').forEach(d => d.classList.remove('open'));
            if (!isOpen) dropdown.classList.add('open');
        });
    });

    document.addEventListener('click', () => {
        document.querySelectorAll('.row-actions-dropdown.open').forEach(d => d.classList.remove('open'));
    });
});

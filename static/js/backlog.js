document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.sprint-group-header').forEach(header => {
        header.addEventListener('click', () => {
            header.closest('.sprint-group').classList.toggle('collapsed');
        });
    });
});

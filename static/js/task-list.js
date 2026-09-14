document.addEventListener('DOMContentLoaded', () => {
    const selectAll = document.querySelector('.task-list-table thead .col-check input');
    const rowChecks = document.querySelectorAll('.task-list-table tbody .col-check input');

    selectAll?.addEventListener('change', () => {
        rowChecks.forEach(cb => { cb.checked = selectAll.checked; });
    });
});

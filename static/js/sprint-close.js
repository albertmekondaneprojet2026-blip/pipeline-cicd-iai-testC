document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.sprint-close-select').forEach(select => {
        const taskId = select.dataset.task;
        const target = document.querySelector(`.sprint-close-target[data-task="${taskId}"]`);
        if (!target) return;

        const sync = () => {
            target.style.display = select.value === 'next_sprint' ? 'inline-block' : 'none';
        };
        select.addEventListener('change', sync);
        sync();
    });
});
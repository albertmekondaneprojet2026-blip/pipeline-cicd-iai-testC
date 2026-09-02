document.addEventListener('DOMContentLoaded', () => {
    const board = document.querySelector('.kanban-board');
    if (!board) return;
    const urlTemplate = board.dataset.updateUrl; // ex: /projects/3/tasks/0/update-status/

    document.querySelectorAll('.kanban-card').forEach(card => {
        card.setAttribute('draggable', 'true');
        card.addEventListener('dragstart', () => card.classList.add('dragging'));
        card.addEventListener('dragend', () => card.classList.remove('dragging'));
    });

    document.querySelectorAll('.kanban-cards').forEach(column => {
        column.addEventListener('dragover', (e) => e.preventDefault());
        column.addEventListener('drop', async (e) => {
            e.preventDefault();
            const dragging = document.querySelector('.kanban-card.dragging');
            if (!dragging) return;
            const taskId = dragging.dataset.taskId;
            const newStatus = column.dataset.status;
            column.appendChild(dragging);

            const url = urlTemplate.replace('/0/', `/${taskId}/`);
            const csrfToken = document.cookie.split('csrftoken=')[1]?.split(';')[0];

            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken },
                body: `status=${newStatus}`,
            });
            if (!response.ok) location.reload();
        });
    });
});
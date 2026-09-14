document.addEventListener('DOMContentLoaded', () => {
    const board = document.querySelector('.kanban-board');
    if (!board) return;
    const baseUrl = board.dataset.updateUrl;

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    const csrftoken = getCookie('csrftoken');

    let dragged = null;

    document.querySelectorAll('.kanban-card').forEach(card => {
        card.setAttribute('draggable', 'true');
        card.addEventListener('dragstart', () => {
            dragged = card;
            card.classList.add('dragging');
        });
        card.addEventListener('dragend', () => card.classList.remove('dragging'));
    });

    document.querySelectorAll('.kanban-cards').forEach(column => {
        column.addEventListener('dragover', (e) => e.preventDefault());
        column.addEventListener('drop', (e) => {
            e.preventDefault();
            if (!dragged) return;
            const newStatus = column.dataset.status;
            column.appendChild(dragged);

            const taskId = dragged.dataset.taskId;
            const url = baseUrl.replace('/0/', `/${taskId}/`);

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken,
                },
                body: `status=${newStatus}`,
            }).then(response => {
                if (!response.ok) location.reload();
            });
        });
    });

    const searchInput = document.getElementById('kanbanSearch');
    searchInput?.addEventListener('input', () => {
        const term = searchInput.value.trim().toLowerCase();
        document.querySelectorAll('.kanban-card').forEach(card => {
            const title = card.querySelector('.kanban-card-title')?.textContent.toLowerCase() || '';
            card.style.display = title.includes(term) ? '' : 'none';
        });
    });
});

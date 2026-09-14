document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('inviteModal');
    const openBtn = document.getElementById('inviteBtn');
    const cancelBtn = document.getElementById('inviteCancel');
    const confirmBtn = document.getElementById('inviteConfirm');
    const emailInput = document.getElementById('inviteEmail');

    const closeModal = () => {
        modal.classList.remove('open');
        emailInput.value = '';
    };

    openBtn?.addEventListener('click', () => modal.classList.add('open'));
    cancelBtn?.addEventListener('click', closeModal);
    modal?.addEventListener('click', (event) => {
        if (event.target === modal) closeModal();
    });

    confirmBtn?.addEventListener('click', () => {
        const email = emailInput.value.trim();
        if (!email) {
            emailInput.focus();
            return;
        }
        // Point d'intégration futur : appel API d'invitation.
        closeModal();
        alert(`Invitation envoyée à ${email}`);
    });

    document.querySelectorAll('.team-card-menu').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.classList.toggle('active');
        });
    });
});

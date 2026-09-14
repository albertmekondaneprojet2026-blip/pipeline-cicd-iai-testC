from .models import Workspace, TeamMember


def get_user_workspace(user):
    """Retourne l'espace de travail principal de l'utilisateur connecte."""
    if not user.is_authenticated:
        return None

    workspace = Workspace.objects.filter(owner=user).first()
    if workspace:
        return workspace

    membership = TeamMember.objects.filter(user=user).select_related('workspace').first()
    return membership.workspace if membership else None

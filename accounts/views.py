#from django.shortcuts import render

# Create your views here.
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.shortcuts import render
from .forms import RegisterForm
from workspaces.models import Workspace, TeamMember


def home_view(request):
    """Ecran 'Accueil' : landing page publique."""
    return render(request, 'accounts/home.html')


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class RateLimitedLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('projects:project_list')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:home')


class RegisterView(CreateView):
    """Ecran 'Inscription' : cree le compte + un Workspace dont l'utilisateur devient admin (logique Jira)."""
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('projects:project_list')

    def form_valid(self, form):
        response = super().form_valid(form)

        workspace = Workspace.objects.create(
            name=form.cleaned_data['workspace_name'],
            owner=self.object,
        )
        TeamMember.objects.create(
            user=self.object,
            workspace=workspace,
            role=TeamMember.Role.ADMIN,
        )

        login(self.request, self.object)
        return response
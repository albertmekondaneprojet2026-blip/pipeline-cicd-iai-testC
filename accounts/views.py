from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm, ContactForm
from workspaces.models import Workspace, TeamMember


def home_view(request):
    """Ecran 'Accueil' : landing page publique."""
    return render(request, 'accounts/home.html')


def about_view(request):
    """Ecran 'A propos'."""
    return render(request, 'accounts/about.html')


def features_view(request):
    """Ecran 'Fonctionnalites'."""
    return render(request, 'accounts/features.html')


def contact_view(request):
    """Ecran 'Contact' avec formulaire."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # NOTE: pas d'envoi d'email reel configure pour l'instant -
            # le message est simplement confirme a l'utilisateur.
            messages.success(request, "Votre message a bien ete envoye. Nous vous repondrons rapidement.")
            return redirect('accounts:contact')
    else:
        form = ContactForm()
    return render(request, 'accounts/contact.html', {'form': form})


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class RateLimitedLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('projects:project_list')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:home')


class RegisterView(CreateView):
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
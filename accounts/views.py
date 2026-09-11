from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm, ContactForm, EmailLoginForm
from workspaces.models import Workspace, TeamMember


def home_view(request):
    return render(request, 'accounts/home.html')


def about_view(request):
    return render(request, 'accounts/about.html')


def features_view(request):
    return render(request, 'accounts/features.html')


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            messages.success(request, "Votre message a bien ete envoye. Nous vous repondrons rapidement.")
            return redirect('accounts:contact')
    else:
        form = ContactForm()
    return render(request, 'accounts/contact.html', {'form': form})


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class RateLimitedLoginView(LoginView):
    form_class = EmailLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('projects:project_list')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:home')


class RegisterView(FormView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('projects:project_list')

    def form_valid(self, form):
        full_name = form.cleaned_data['full_name']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password1']

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name,
        )

        workspace = Workspace.objects.create(
            name=f"Espace de {full_name}",
            owner=user,
        )
        TeamMember.objects.create(
            user=user,
            workspace=workspace,
            role=TeamMember.Role.ADMIN,
        )

        login(self.request, user)
        return super().form_valid(form)
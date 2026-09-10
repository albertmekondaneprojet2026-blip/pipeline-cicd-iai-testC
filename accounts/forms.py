from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    workspace_name = forms.CharField(
        max_length=100,
        label="Nom de votre espace de travail",
        widget=forms.TextInput(attrs={'placeholder': 'Ex : TaskFlow Studio'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'workspace_name', 'password1', 'password2']


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, label="Nom")
    email = forms.EmailField(label="Adresse e-mail")
    subject = forms.CharField(max_length=150, label="Sujet")
    message = forms.CharField(widget=forms.Textarea, label="Message")
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError


class EmailLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email professionnel",
        widget=forms.TextInput(
            attrs={
                'placeholder': 'vous@entreprise.com',
                'autofocus': True
            }
        )
    )

    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '••••••••••••'
            }
        )
    )


class RegisterForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        label="Nom complet",
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Votre nom complet'
            }
        )
    )

    email = forms.EmailField(
        label="Email professionnel",
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'vous@entreprise.com'
            }
        )
    )

    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '••••••••••••'
            }
        )
    )

    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '••••••••••••'
            }
        )
    )

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "Un compte existe deja avec cet email."
            )

        return email

    def clean(self):
        cleaned = super().clean()

        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')

        if p1 and p2 and p1 != p2:
            self.add_error(
                'password2',
                "Les mots de passe ne correspondent pas."
            )

        elif p1:
            try:
                validate_password(p1)
            except DjangoValidationError as e:
                self.add_error('password1', e.messages)

        return cleaned


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label="Nom",
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Votre nom'
            }
        )
    )

    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'vous@entreprise.com'
            }
        )
    )

    subject = forms.CharField(
        max_length=200,
        label="Sujet",
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Objet de votre message'
            }
        )
    )

    message = forms.CharField(
        label="Message",
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Écrivez votre message...',
                'rows': 6
            }
        )
    )
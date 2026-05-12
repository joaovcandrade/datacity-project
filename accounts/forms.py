from __future__ import annotations

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Nome de usuário", "class": "form-control"}),
        label="Nome de Usuário",
    )
    nome = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Nome completo", "class": "form-control"}),
        label="Nome Completo",
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "seu@email.com", "class": "form-control"}),
        label="E-mail",
    )
    cpf = forms.CharField(
        max_length=14,
        required=True,
        widget=forms.TextInput(attrs={
            "placeholder": "000.000.000-00",
            "class": "form-control",
            "pattern": r"\d{3}\.\d{3}\.\d{3}-\d{2}",
        }),
        label="CPF",
        help_text="Formato: 000.000.000-00",
    )
    cidade = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Sua cidade", "class": "form-control"}),
        label="Cidade",
    )
    user_type = forms.ChoiceField(
        choices=User.UserType.choices,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Tipo de Usuário",
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Senha", "class": "form-control"}),
        label="Senha",
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirme a senha", "class": "form-control"}),
        label="Confirmar Senha",
    )

    class Meta:
        model = User
        fields = ["username", "nome", "email", "cpf", "cidade", "user_type", "password1", "password2"]


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="E-mail ou Usuário",
        widget=forms.TextInput(attrs={"placeholder": "E-mail ou usuário", "class": "form-control"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Senha", "class": "form-control"}),
        label="Senha",
    )

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        label="Nome de Usuário",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "nome.usuario"}),
    )
    nome = forms.CharField(
        max_length=100,
        label="Nome Completo",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Seu nome completo"}),
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "seu@email.com"}),
    )
    cpf = forms.CharField(
        max_length=14,
        label="CPF",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "000.000.000-00",
        }),
    )
    cidade = forms.CharField(
        max_length=100,
        label="Cidade",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    user_type = forms.ChoiceField(
        choices=User.UserType.choices,
        label="Tipo de Usuário",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    password1 = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirmar Senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ["username", "nome", "email", "cpf", "cidade", "user_type", "password1", "password2"]

    def clean_cpf(self) -> str:
        """Valida formato básico do CPF (validação de dígitos deve ser feita por biblioteca específica)."""
        cpf = self.cleaned_data.get("cpf", "").strip()
        digits = cpf.replace(".", "").replace("-", "")
        if not digits.isdigit() or len(digits) != 11:
            raise forms.ValidationError("CPF inválido. Informe no formato 000.000.000-00.")
        return cpf


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=254,
        label="E-mail ou Usuário",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "seu@email.com",
            "autofocus": True,
        }),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

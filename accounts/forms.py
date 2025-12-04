from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite seu nome de usuário',
            'class': 'form-control'
        }),
        label='Nome de Usuário'
    )
    nome = forms.CharField(
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite seu nome completo',
            'class': 'form-control'
        }),
        label='Nome Completo'
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Digite seu email',
            'class': 'form-control'
        }),
        label='Email'
    )
    cpf = forms.CharField(
        max_length=14, 
        required=True, 
        widget=forms.TextInput(attrs={
            'placeholder': '000.000.000-00',
            'class': 'form-control',
            'pattern': r'\d{3}\.\d{3}\.\d{3}-\d{2}'
        }),
        label='CPF',
        help_text='Formato: 000.000.000-00'
    )
    cidade = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite sua cidade',
            'class': 'form-control'
        }),
        label='Cidade'
    )
    categoria = forms.ChoiceField(
        choices=User.CategoriaChoices.choices,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Categoria'
    )
    user_type = forms.ChoiceField(
        choices=User.UserType.choices, 
        required=True, 
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Tipo de Usuário'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Digite sua senha',
            'class': 'form-control'
        }),
        label='Senha'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirme sua senha',
            'class': 'form-control'
        }),
        label='Confirmar Senha'
    )

    class Meta:
        model = User
        fields = ['username', 'nome', 'email', 'cpf', 'cidade', 'categoria', 'password1', 'password2', 'user_type']

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=50,
        label='Email ou Usuário',
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite seu email ou nome de usuário',
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Digite sua senha',
            'class': 'form-control'
        }),
        label='Senha'
    )
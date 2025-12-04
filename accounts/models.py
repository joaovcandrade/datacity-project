from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class UserType(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        MANAGER = 'MANAGER', 'Gestor'
        COMMON = 'COMMON', 'Usuário Comum'

    # Usando o campo id padrão do Django
    nome = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    
    # Configurando email como campo de autenticação
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    cpf = models.CharField(max_length=14, null=True, blank=True)  # CPF com formatação (000.000.000-00)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    class CategoriaChoices(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        MANAGER = 'MANAGER', 'Gestor'
        COMMON = 'COMMON', 'Usuário'

    categoria = models.CharField(
        max_length=10,
        choices=CategoriaChoices.choices,
        null=True,
        blank=True
    )
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.COMMON
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Adicionando related_name para resolver conflitos
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def is_admin(self):
        return self.user_type == self.UserType.ADMIN

    def is_manager(self):
        return self.user_type == self.UserType.MANAGER

    def is_common_user(self):
        return self.user_type == self.UserType.COMMON

    def __str__(self):
        return self.username

class Platform(models.Model):
    id_plataforma = models.AutoField(primary_key=True)  # Chave primária personalizada
    Nome = models.CharField(max_length=100, unique=True)
    Direcionamento = models.URLField()
    
    class Meta:
        ordering = ['Nome']
        db_table = 'plataforma'

    def __str__(self): 
        return self.Nome

class Norm(models.Model):
    id_norma = models.AutoField(primary_key=True)  # Chave primária personalizada
    Nome = models.CharField(max_length=100, unique=True)
    Direcionamento = models.URLField()

    class Meta:
        ordering = ['Nome']
        db_table = 'norma'

    def __str__(self):
        return self.Nome

class ISO37120Indicator(models.Model):
    id = models.AutoField(primary_key=True)
    categoria = models.CharField(max_length=100)
    nome_indicador = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=[
        ('core', 'Principal'),
        ('supporting', 'Apoio'),
        ('profile', 'Perfil')
    ])
    ods = models.CharField(max_length=10)
    unidade = models.CharField(max_length=50)

    # Dados para diferentes anos
    dado_2022 = models.CharField(max_length=100, null=True, blank=True)
    dado_2023 = models.CharField(max_length=100, null=True, blank=True)
    dado_2024 = models.CharField(max_length=100, null=True, blank=True)
    dado_2025 = models.CharField(max_length=100, null=True, blank=True)

    # Fontes para diferentes anos
    fonte_2022 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2023 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2024 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2025 = models.CharField(max_length=500, null=True, blank=True)

    # Anexos PDF para diferentes anos
    anexo_2022 = models.FileField(upload_to='iso37120/anexos/', null=True, blank=True)
    anexo_2023 = models.FileField(upload_to='iso37120/anexos/', null=True, blank=True)
    anexo_2024 = models.FileField(upload_to='iso37120/anexos/', null=True, blank=True)
    anexo_2025 = models.FileField(upload_to='iso37120/anexos/', null=True, blank=True)

    # Cidade para permitir dados de múltiplas cidades
    cidade = models.CharField(max_length=100, default='Londrina')
    estado = models.CharField(max_length=50, default='PR')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'iso37120_indicators'
        ordering = ['categoria', 'nome_indicador']
        unique_together = ['nome_indicador', 'cidade', 'estado']

    def __str__(self):
        return f"{self.nome_indicador} - {self.cidade}/{self.estado}"

class ISO37122Indicator(models.Model):
    id = models.AutoField(primary_key=True)
    categoria = models.CharField(max_length=100)
    nome_indicador = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=[
        ('core', 'Principal'),
        ('supporting', 'Apoio'),
        ('profile', 'Perfil')
    ])
    ods = models.CharField(max_length=10)
    unidade = models.CharField(max_length=50)

    # Dados para diferentes anos
    dado_2022 = models.CharField(max_length=100, null=True, blank=True)
    dado_2023 = models.CharField(max_length=100, null=True, blank=True)
    dado_2024 = models.CharField(max_length=100, null=True, blank=True)
    dado_2025 = models.CharField(max_length=100, null=True, blank=True)

    # Fontes para diferentes anos
    fonte_2022 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2023 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2024 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2025 = models.CharField(max_length=500, null=True, blank=True)

    # Anexos PDF para diferentes anos
    anexo_2022 = models.FileField(upload_to='iso37122/anexos/', null=True, blank=True)
    anexo_2023 = models.FileField(upload_to='iso37122/anexos/', null=True, blank=True)
    anexo_2024 = models.FileField(upload_to='iso37122/anexos/', null=True, blank=True)
    anexo_2025 = models.FileField(upload_to='iso37122/anexos/', null=True, blank=True)

    # Cidade para permitir dados de múltiplas cidades
    cidade = models.CharField(max_length=100, default='Londrina')
    estado = models.CharField(max_length=50, default='PR')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'iso37122_indicators'
        ordering = ['categoria', 'nome_indicador']
        unique_together = ['nome_indicador', 'cidade', 'estado']

    def __str__(self):
        return f"{self.nome_indicador} - {self.cidade}/{self.estado}"

class ISO37123Indicator(models.Model):
    id = models.AutoField(primary_key=True)
    categoria = models.CharField(max_length=100)
    nome_indicador = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=[
        ('core', 'Principal'),
        ('supporting', 'Apoio'),
        ('profile', 'Perfil')
    ])
    ods = models.CharField(max_length=10)
    unidade = models.CharField(max_length=50)

    # Dados para diferentes anos
    dado_2022 = models.CharField(max_length=100, null=True, blank=True)
    dado_2023 = models.CharField(max_length=100, null=True, blank=True)
    dado_2024 = models.CharField(max_length=100, null=True, blank=True)
    dado_2025 = models.CharField(max_length=100, null=True, blank=True)

    # Fontes para diferentes anos
    fonte_2022 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2023 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2024 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2025 = models.CharField(max_length=500, null=True, blank=True)

    # Anexos PDF para diferentes anos
    anexo_2022 = models.FileField(upload_to='iso37123/anexos/', null=True, blank=True)
    anexo_2023 = models.FileField(upload_to='iso37123/anexos/', null=True, blank=True)
    anexo_2024 = models.FileField(upload_to='iso37123/anexos/', null=True, blank=True)
    anexo_2025 = models.FileField(upload_to='iso37123/anexos/', null=True, blank=True)

    # Cidade para permitir dados de múltiplas cidades
    cidade = models.CharField(max_length=100, default='Londrina')
    estado = models.CharField(max_length=50, default='PR')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'iso37123_indicators'
        ordering = ['categoria', 'nome_indicador']
        unique_together = ['nome_indicador', 'cidade', 'estado']

    def __str__(self):
        return f"{self.nome_indicador} - {self.cidade}/{self.estado}"

class ISO37125Indicator(models.Model):
    id = models.AutoField(primary_key=True)
    categoria = models.CharField(max_length=100)
    nome_indicador = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=[
        ('core', 'Principal'),
        ('supporting', 'Apoio'),
        ('profile', 'Perfil')
    ])
    ods = models.CharField(max_length=10)
    unidade = models.CharField(max_length=50)

    # Dados para diferentes anos
    dado_2022 = models.CharField(max_length=100, null=True, blank=True)
    dado_2023 = models.CharField(max_length=100, null=True, blank=True)
    dado_2024 = models.CharField(max_length=100, null=True, blank=True)
    dado_2025 = models.CharField(max_length=100, null=True, blank=True)

    # Fontes para diferentes anos
    fonte_2022 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2023 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2024 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2025 = models.CharField(max_length=500, null=True, blank=True)

    # Anexos PDF para diferentes anos
    anexo_2022 = models.FileField(upload_to='iso37125/anexos/', null=True, blank=True)
    anexo_2023 = models.FileField(upload_to='iso37125/anexos/', null=True, blank=True)
    anexo_2024 = models.FileField(upload_to='iso37125/anexos/', null=True, blank=True)
    anexo_2025 = models.FileField(upload_to='iso37125/anexos/', null=True, blank=True)

    # Cidade para permitir dados de múltiplas cidades
    cidade = models.CharField(max_length=100, default='Londrina')
    estado = models.CharField(max_length=50, default='PR')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'iso37125_indicators'
        ordering = ['categoria', 'nome_indicador']
        unique_together = ['nome_indicador', 'cidade', 'estado']

    def __str__(self):
        return f"{self.nome_indicador} - {self.cidade}/{self.estado}"
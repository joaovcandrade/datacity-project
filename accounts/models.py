from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField


#Models principais (necessários para o funcionamento de outros models).
class Municipality(models.Model):
    nome = models.CharField(max_length=150)
    estado = models.CharField(max_length=70, null=True)
    codigo_ibge = models.CharField(max_length=20, unique=True, db_index=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'municipio'

    def __str__(self):
        return f'{self.nome}/{self.estado}'



class User(AbstractUser):
    class UserType(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        MANAGER = 'MANAGER', 'Gestor'
        COMMON = 'COMMON', 'Usuário Comum'

    nome = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    cpf = models.CharField(max_length=14, null=True, blank=True, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class CategoriaChoices(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        MANAGER = 'MANAGER', 'Gestor'
        COMMON = 'COMMON', 'Usuário'

    categoria = models.CharField(
        max_length=10,
        choices=CategoriaChoices.choices,
        null=True,
        blank=True,
        db_index=True
    )
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.COMMON,
        db_index=True
    )

    municipio = models.ForeignKey(
        Municipality,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
        db_column="FK_municipio_id",
    )

    ativo = models.BooleanField(default=True, db_index=True)

    senha_temporaria_ativa = models.BooleanField(default=True, db_index=True)
    token_recuperacao = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    data_token_recuperacao = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

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

    class Meta:
        db_table = 'usuario'

    def is_admin(self):
        return self.user_type == self.UserType.ADMIN

    def is_manager(self):
        return self.user_type == self.UserType.MANAGER

    def is_common_user(self):
        return self.user_type == self.UserType.COMMON

    def __str__(self):
        return self.username
    


class YearReference(models.Model):
    ano = models.PositiveIntegerField(unique=True, db_index=True)
    ativo = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'ano_referencia'
        ordering = ['ano']

    def __str__(self):
        return str(self.ano)




#Models Normas ISO
class NormISO(models.Model):
    codigo_norma = models.CharField(max_length=30, db_index=True)
    descricao = models.TextField(blank=True, null=True)
    ano_referencia = models.ForeignKey(
        YearReference,
        on_delete=models.CASCADE,
        db_column="FK_ano_referencia_id"
    )

    class Meta:
        db_table = 'norma_iso'
        ordering = ['codigo_norma']

    def __str__(self):
        return self.codigo_norma



class Category(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    norma_iso = models.ForeignKey(
        NormISO,
        on_delete=models.CASCADE,
        db_column="FK_norma_iso_id",
    )

    class Meta:
        db_table = 'categoria'
        ordering = ['nome']

    def __str__(self):
        return self.nome



class Indicator(models.Model):
    class TipoChoices(models.TextChoices):
        PRINCIPAL = 'principal', 'Principal'
        APOIO = 'apoio', 'Apoio'
        PERFIL = 'perfil', 'Perfil'
    nome = models.CharField(max_length=255, null=True, blank=True)
    descricao = models.CharField(max_length=100, null=True, blank=True)
    tipo = models.CharField(
        max_length=20,
        choices=TipoChoices.choices,
        db_index=True
    )
    ods = ArrayField(models.CharField(max_length=50), blank=True, default=list)
    unidade_medida = models.CharField(max_length=100, null=True, blank=True)
    opcoes_predefinidas = models.JSONField(null=True, blank=True)
    direcao_melhoria = models.IntegerField(blank=True, null=True)
    categoria = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        db_column="FK_categoria_id",
    )

    class Meta:
        db_table = 'indicador'
        ordering = ['nome']

    def __str__(self):
        return self.nome



class IndicatorValueYear(models.Model):
    valor_numerico = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    valor_texto = models.TextField(null=True, blank=True)
    fonte = models.CharField(max_length=255, null=True, blank=True)
    indicador = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        db_column="FK_indicador_id",
    )
    municipio = models.ForeignKey(
        Municipality,
        on_delete=models.CASCADE,
        db_column="FK_municipio_id",
    )

    class Meta:
        db_table = 'valor_indicador_ano'

    def __str__(self):
        return f'{self.indicador} - {self.municipio}'



class EvidencePDF(models.Model):
    descricao = models.CharField(max_length=255, null=True, blank=True)
    caminho_arquivo = models.CharField(max_length=500)
    data_upload = models.DateTimeField(auto_now_add=True)
    valor_indicador_ano = models.ForeignKey(
        IndicatorValueYear,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'evidencia_pdf_iso'

    def __str__(self):
        return self.caminho_arquivo
    

    
class Certification(models.Model):
    id = models.BigAutoField(primary_key=True)
    nivel = models.CharField(max_length=100)
    requisitos = models.JSONField(null=True, blank=True)
    norma_iso = models.ForeignKey(
        NormISO,
        on_delete=models.CASCADE,
        db_column="FK_norma_iso_id",
        related_name="certification",
    )

    class Meta:
        db_table = "certificacao"
        verbose_name = "Certificação"
        verbose_name_plural = "Certificações"

    def __str__(self):
        return f"{self.norma_iso.codigo_norma} - {self.nivel}"




#Models Levantamento Futuro CSC
class CategoriaCSC(models.Model):
    nome = models.CharField(max_length=255)

    class Meta:
        db_table = "categoria_CSC"
        verbose_name = "Categoria CSC"
        verbose_name_plural = "Categorias CSC"

    def __str__(self):
        return self.nome



class FutureIndicatorCSC(models.Model):
    nome_indicador = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)
    opcoes_predefinidas = models.JSONField(null=True, blank=True)
    ods = models.CharField(max_length=10)
    unidade_medida = models.CharField(max_length=50)
    categoria = models.ForeignKey(
        CategoriaCSC,
        on_delete=models.CASCADE,
        db_column="FK_categoria_CSC_id",
    )
    ano_referencia = models.ForeignKey(
        YearReference,
        on_delete=models.CASCADE,
        db_column="FK_ano_referencia_id",
    )

    class Meta:
        db_table = "indicador_futuro_CSC"
        verbose_name = "Indicador Futuro CSC"
        verbose_name_plural = "Indicadores Futuros CSC"

    def __str__(self):
        return self.nome_indicador



class FutureIndicatorValueCSC(models.Model):
    valor_numerico = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    valor_texto = models.CharField(max_length=100, blank=True, null=True)
    fonte = models.CharField(max_length=500, blank=True, null=True)
    indicador_futuro = models.ForeignKey(
        FutureIndicatorCSC,
        on_delete=models.CASCADE,
        db_column="FK_indicador_futuro_CSC_id",
    )
    municipio = models.ForeignKey(
        Municipality,
        on_delete=models.CASCADE,
        db_column="FK_municipio_id",
    )

    class Meta:
        db_table = "levantamento_futuro_CSC"
        verbose_name = "Levantamento Futuro CSC"
        verbose_name_plural = "Levantamentos Futuros CSC"

    def __str__(self):
        return self.indicador_futuro.nome_indicador



class EvidencePDFCSC(models.Model):
    descricao = models.CharField(max_length=255, blank=True, null=True)
    caminho_arquivo = models.CharField(max_length=500)
    data_upload = models.DateTimeField(auto_now_add=True)
    levantamento_futuro = models.ForeignKey(
        FutureIndicatorValueCSC,
        on_delete=models.CASCADE,
        db_column="FK_levantamento_futuro_CSC_id",
    )

    class Meta:
        db_table = "evidencia_pdf_CSC"
        verbose_name = "Evidência PDF CSC"
        verbose_name_plural = "Evidências PDF CSC"

    def __str__(self):
        return self.descricao or "Evidência PDF CSC"





#Models do ranking
class MunicipalityRanking(models.Model):
    pontuacao_total_categoria = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    indicadores_preenchidos = models.PositiveIntegerField(default=0)
    indicadores_totais = models.PositiveIntegerField(default=0)
    cor_classificacao = models.CharField(max_length=50, null=True, blank=True)
    data_calculo = models.DateTimeField(auto_now=True)
    municipio = models.ForeignKey(
        Municipality,
        on_delete=models.CASCADE,
        related_name='rankings'
    )
    categoria = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='rankings'
    )

    class Meta:
        db_table = 'ranking_municipios'
        
    def __str__(self):
        return self.municipio
    




#Models Consulta Cidades
class ExternalAPIData(models.Model):
    origem_api = models.CharField(max_length=100)
    tipo_dado = models.CharField(max_length=100)
    dados_json = models.JSONField()
    data_coleta = models.DateTimeField()
    valido_ate = models.DateTimeField()
    municipio = models.ForeignKey(
        Municipality,
        on_delete=models.CASCADE,
        db_column="municipio_id",
        related_name="external_data",
    )

    class Meta:
        db_table = "dados_externos_api"
        verbose_name = "Dado Externo de API"
        verbose_name_plural = "Dados Externos de APIs"

    def __str__(self):
        return f"Dados {self.origem_api} - {self.municipio.nome}"

    def is_data_valid(self):
        from django.utils import timezone

        return self.valido_ate > timezone.now()




        












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
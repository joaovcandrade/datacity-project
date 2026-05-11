from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField


#Models principais (necessários para o funcionamento de outros models).
class Municipality(models.Model):
    nome = models.CharField(max_length=150)
    estado = models.CharField(max_length=70, null=True, blank=True)
    subdivision_id = models.CharField(max_length=10, null=True, blank=True, db_index=True)
    codigo_ibge = models.CharField(max_length=20, unique=True, db_index=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    regiao = models.CharField(max_length=50, verbose_name="Região", null=True, blank=True)
    porte = models.CharField(max_length=50, verbose_name="Porte da Cidade", null=True, blank=True)

    class Meta:
        db_table = 'municipio'
        verbose_name = 'Município'
        verbose_name_plural = 'Municípios'

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

    criado_por = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_criados',
        help_text='Usuário administrador ou gestor que criou esta conta.',
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
        ordering = ['-ano']

    def __str__(self):
        return str(self.ano)



class Platform(models.Model):
    nome = models.CharField(max_length=150)

    ano_referencia = models.ForeignKey(
        YearReference,
        on_delete=models.CASCADE,
        db_column="FK_ano_referencia_id",
        related_name="plataformas",
    )

    class Meta:
        db_table = "plataforma"
        verbose_name = "Plataforma"
        verbose_name_plural = "Plataformas"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} - {self.ano_referencia}"
    
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
    descricao = models.CharField(max_length=255, null=True, blank=True)

    norma_iso = models.ForeignKey(
        NormISO,
        on_delete=models.CASCADE,
        db_column="FK_norma_iso_id",
        related_name="categorias",
        null=True,
        blank=True,
    )

    plataforma = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        db_column="FK_plataforma_id",
        related_name="categorias",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "categoria"
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["nome"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(norma_iso__isnull=False) |
                    models.Q(plataforma__isnull=False)
                ),
                name="categoria_tem_norma_ou_plataforma",
            )
        ]

    def __str__(self):
        return self.nome



class Indicator(models.Model):
    class TipoChoices(models.TextChoices):
        PRINCIPAL = "principal", "Principal"
        APOIO = "apoio", "Apoio"
        PERFIL = "perfil", "Perfil"

    nome = models.CharField(max_length=255)
    descricao = models.CharField(max_length=255, null=True, blank=True)

    tipo = models.CharField(
        max_length=20,
        choices=TipoChoices.choices,
        db_index=True,
    )

    opcoes_predefinidas = models.JSONField(null=True, blank=True)
    unidade_medida = models.CharField(max_length=100, null=True, blank=True)
    direcao_melhoria = models.IntegerField(null=True, blank=True)

    valor_referencia_minimo = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    valor_referencia_maximo = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    fonte_valor_referencia = models.CharField(max_length=255, null=True, blank=True)

    ativo = models.BooleanField(default=True, db_index=True)
    deletado = models.BooleanField(default=False, db_index=True)
    deletado_em = models.DateTimeField(null=True, blank=True)
    deletado_por = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="indicadores_deletados"
    )

    ods = ArrayField(
        models.IntegerField(),
        blank=True,
        default=list,
    )

    categorias = models.ManyToManyField(
        Category,
        through="IndicatorCategory",
        related_name="indicadores",
        blank=True,
    )

    class Meta:
        db_table = "indicador"
        verbose_name = "Indicador"
        verbose_name_plural = "Indicadores"
        ordering = ["nome"]

    def __str__(self):
        return self.nome
    


class IndicatorCategory(models.Model):
    indicador = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        db_column="FK_indicador_id",
        related_name="indicador_categorias",
    )

    categoria = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        db_column="FK_categoria_id",
        related_name="categoria_indicadores",
    )

    class Meta:
        db_table = "indicador_categoria"
        verbose_name = "Indicador Categoria"
        verbose_name_plural = "Indicadores Categorias"
        constraints = [
            models.UniqueConstraint(
                fields=["indicador", "categoria"],
                name="uniq_indicador_categoria",
            )
        ]

    def __str__(self):
        return f"{self.indicador} - {self.categoria}"



class IndicatorValueYear(models.Model):
    valor_numerico = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    valor_texto = models.CharField(max_length=255, null=True, blank=True)
    fonte = models.CharField(max_length=255, null=True, blank=True)

    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="valores_indicadores_atualizados"
    )

    indicador = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        db_column="FK_indicador_id",
        related_name="valores_ano",
    )

    municipio = models.ForeignKey(
        Municipality,
        on_delete=models.CASCADE,
        db_column="FK_municipio_id",
        related_name="valores_indicadores",
    )

    class Meta:
        db_table = "valor_indicador_ano"
        verbose_name = "Valor do Indicador por Ano"
        verbose_name_plural = "Valores dos Indicadores por Ano"
        indexes = [
            models.Index(fields=["municipio", "indicador"]),
        ]

    def __str__(self):
        return f"{self.indicador} - {self.municipio}"



class EvidencePDF(models.Model):
    descricao = models.CharField(max_length=255, null=True, blank=True)
    caminho_arquivo = models.CharField(max_length=500)
    data_upload = models.DateTimeField(auto_now_add=True)

    apagado = models.BooleanField(default=False, db_index=True)
    apagado_em = models.DateTimeField(null=True, blank=True)
    apagado_por = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evidencias_apagadas"
    )

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



# model dos logs de auditoria
class AuditLog(models.Model):
    class AcaoChoices(models.TextChoices):
        ANEXO_APAGADO = "ANEXO_APAGADO", "Anexo apagado"
        VALOR_ALTERADO = "VALOR_ALTERADO", "Valor alterado"
        INDICADOR_EDITADO = "INDICADOR_EDITADO", "Indicador editado"
        INDICADOR_DELETADO = "INDICADOR_DELETADO", "Indicador deletado"
        RECUPERACAO = "RECUPERACAO", "Recuperação"
        ANEXO_ENVIADO = "ANEXO_ENVIADO", "Anexo enviado"
        DESIGNACAO_CRIADA = "DESIGNACAO_CRIADA", "Designação criada"
        DESIGNACAO_CANCELADA = "DESIGNACAO_CANCELADA", "Designação cancelada"
        PREENCHIMENTO_DESIGNADO = "PREENCHIMENTO_DESIGNADO", "Preenchimento designado"

    usuario = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs_auditoria"
    )

    acao = models.CharField(max_length=50, choices=AcaoChoices.choices)

    objeto_tipo = models.CharField(max_length=100)
    objeto_id = models.PositiveIntegerField(null=True, blank=True)

    descricao = models.TextField(blank=True, null=True)

    dados_anteriores = models.JSONField(null=True, blank=True)
    dados_novos = models.JSONField(null=True, blank=True)

    recuperavel = models.BooleanField(default=False)
    recuperado = models.BooleanField(default=False)

    recuperado_por = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs_auditoria_recuperados"
    )

    recuperado_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "log_auditoria"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.acao} - {self.objeto_tipo} #{self.objeto_id}"
    


#models de designação de responsáveis por indicadores
class DesignacaoPreenchimento(models.Model):
    class StatusChoices(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
        CONCLUIDA = "CONCLUIDA", "Concluída"
        CANCELADA = "CANCELADA", "Cancelada"

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(null=True, blank=True)

    gestor_responsavel = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="designacoes_recebidas"
    )

    criado_por = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="designacoes_criadas"
    )

    municipio = models.ForeignKey(
        "Municipality",
        on_delete=models.CASCADE,
        related_name="designacoes_preenchimento"
    )

    indicadores = models.ManyToManyField(
        "Indicator",
        through="DesignacaoIndicador",
        related_name="designacoes_preenchimento"
    )

    prazo = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDENTE,
        db_index=True
    )

    ativa = models.BooleanField(default=True, db_index=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    concluida_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "designacao_preenchimento"
        ordering = ["-criado_em"]
        permissions = [
            ("acesso_total_designacao", "Pode gerenciar todas as designações de preenchimento"),
        ]

    def __str__(self):
        return self.titulo


class DesignacaoIndicador(models.Model):
    designacao = models.ForeignKey(
        DesignacaoPreenchimento,
        on_delete=models.CASCADE,
        related_name="itens"
    )

    indicador = models.ForeignKey(
        "Indicator",
        on_delete=models.CASCADE,
        related_name="itens_designacao"
    )

    obrigatorio = models.BooleanField(default=True)
    preenchido = models.BooleanField(default=False)

    valor_indicador = models.ForeignKey(
        "IndicatorValueYear",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itens_designacao"
    )

    preenchido_por = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="indicadores_designados_preenchidos"
    )

    preenchido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "designacao_indicador"
        constraints = [
            models.UniqueConstraint(
                fields=["designacao", "indicador"],
                name="uniq_designacao_indicador"
            )
        ]

    def __str__(self):
        return f"{self.designacao} - {self.indicador}"




class PlatformGoalReference(models.Model):
    platform = models.ForeignKey(
        "Platform",
        on_delete=models.CASCADE,
        related_name="goal_references",
    )
    municipio = models.ForeignKey(
        "Municipality",
        on_delete=models.CASCADE,
        related_name="platform_goal_references_definidas",
        null=True,
        blank=True,
        help_text="Município para o qual a meta vale. A referência é compartilhada por todos os gestores desse município.",
    )
    gestor = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="platform_goal_references",
        help_text="Usuário que definiu ou atualizou a meta.",
    )
    municipio_referencia = models.ForeignKey(
        "Municipality",
        on_delete=models.CASCADE,
        related_name="platform_goal_references",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "plataforma_meta_referencia"
        verbose_name = "Meta de referência da plataforma"
        verbose_name_plural = "Metas de referência das plataformas"
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "municipio"],
                name="uniq_meta_referencia_platform_municipio",
            )
        ]

    def __str__(self):
        municipio_nome = self.municipio.nome if self.municipio else "Sem município"
        referencia_nome = self.municipio_referencia.nome if self.municipio_referencia else "Sem referência"
        return f"{self.platform} - {municipio_nome} -> {referencia_nome}"

    def __str__(self):
        return f"{self.platform} - {self.gestor} - {self.municipio_referencia}"


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
        db_table = "ranking_municipios"
        verbose_name = "Ranking de Município"
        verbose_name_plural = "Rankings de Municípios"
        indexes = [
            models.Index(fields=["municipio", "categoria"]),
        ]

    def __str__(self):
        return f"{self.municipio} - {self.categoria}"
    


class RankingISOCategoriaView(models.Model):
    municipio_id = models.BigIntegerField()
    municipio = models.CharField(max_length=150)
    uf = models.CharField(max_length=70)

    ano = models.PositiveIntegerField()

    norma_id = models.BigIntegerField()
    codigo_norma = models.CharField(max_length=30)

    categoria_id = models.BigIntegerField()
    categoria = models.CharField(max_length=100)

    pontuacao_categoria = models.DecimalField(max_digits=14, decimal_places=4)
    indicadores_preenchidos = models.PositiveIntegerField()
    indicadores_totais = models.PositiveIntegerField()
    cor_classificacao = models.CharField(max_length=50, null=True, blank=True)
    data_calculo = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "vw_ranking_iso_categoria"
    



#Models Consulta Cidades
class ExternalAPIData(models.Model):
    origem_api = models.CharField(max_length=100)
    tipo_dado = models.CharField(max_length=100)
    dados_json = models.JSONField()
    data_coleta = models.DateTimeField(auto_now_add=True)
    valido_ate = models.DateTimeField(null=True, blank=True)

    municipio = models.ForeignKey(
        Municipality,
        on_delete=models.CASCADE,
        db_column="FK_municipio_id",
        related_name="dados_externos_api",
    )

    class Meta:
        db_table = "dados_externos_api"
        verbose_name = "Dado Externo API"
        verbose_name_plural = "Dados Externos API"
        ordering = ["-data_coleta"]

    def __str__(self):
        return f"{self.origem_api} - {self.tipo_dado} - {self.municipio}"

    def is_data_valid(self):
        from django.utils import timezone

        return self.valido_ate > timezone.now()




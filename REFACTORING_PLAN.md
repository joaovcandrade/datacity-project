# Plano de Refatoração — DataCity Project

> Gerado em: 2026-05-12  
> Baseado em: Revisão arquitetural completa  
> Objetivo: Transformar o projeto em um sistema production-ready, seguro, escalável e manutenível

---

## Status do Projeto Atual

| Critério            | Nota  | Situação                                      |
|---------------------|-------|-----------------------------------------------|
| Arquitetura         | 2.5/10 | God App, sem camadas, sem separação de contexto |
| Segurança           | 2/10  | `setattr` arbitrário, DEBUG=True, credenciais hardcoded |
| Qualidade de Código | 3/10  | 2108 linhas em um views.py, duplicação massiva |
| Escalabilidade      | 2/10  | Mock data em memória, sem cache, sem async     |
| Testes              | 0/10  | Zero testes reais                             |
| Organização         | 3/10  | Responsabilidades misturadas em apps errados  |

---

## Fases de Execução

```
FASE 1 → FASE 2 → FASE 3 → FASE 4 → FASE 5 → FASE 6 → FASE 7 → FASE 8 → FASE 9 → FASE 10
Segurança  Settings  Models  Apps     DRF      Testes   Perf     Qualidade Bootstrap  Docker
(crítico)  (crítico) (core)  (arch)   (API)    (sempre) (infra)  (code)    (frontend) (infra)
```

---

## FASE 1 — Correções de Segurança Críticas
> **Prioridade: BLOQUEANTE** — fazer antes de qualquer deploy  
> **Estimativa: 1-2 dias**  
> Nenhuma outra fase deve começar com esses problemas abertos.

---

### 1.1 — Whitelist no `setattr` (Vulnerabilidade ativa)

**Arquivo:** `accounts/views.py`  
**Risco:** CRÍTICO — usuário MANAGER pode sobrescrever qualquer campo do model via API

**Problema:**
```python
# ATUAL — qualquer field_name é aceito
indicator = ISO37120Indicator.objects.get(id=indicator_id)
setattr(indicator, field_name, field_value)  # field_name vem do request!
indicator.save()
```

**Correção:**
```python
ALLOWED_UPDATE_FIELDS = frozenset({
    'dado_2022', 'dado_2023', 'dado_2024', 'dado_2025',
    'fonte_2022', 'fonte_2023', 'fonte_2024', 'fonte_2025',
})

if field_name not in ALLOWED_UPDATE_FIELDS:
    return JsonResponse({'success': False, 'message': 'Campo não permitido'}, status=400)

setattr(indicator, field_name, field_value)
indicator.save(update_fields=[field_name, 'updated_at'])
```

**Aplicar em:** `update_iso37120_field`, `update_iso37122_field`, `update_iso37123_field`, `update_iso37125_field`

---

### 1.2 — Validação de `year` nos endpoints de anexo

**Arquivo:** `accounts/views.py`  
**Risco:** CRÍTICO — `year` não validado permite setar atributos arbitrários via `f'anexo_{year}'`

**Problema:**
```python
year = request.POST.get('year')         # sem validação
anexo_field = f'anexo_{year}'           # year pode ser qualquer coisa
setattr(indicator, anexo_field, file)   # atributo arbitrário
```

**Correção:**
```python
VALID_YEARS = frozenset({'2022', '2023', '2024', '2025'})

year = request.POST.get('year')
if year not in VALID_YEARS:
    return JsonResponse({'success': False, 'message': 'Ano inválido'}, status=400)
```

**Aplicar em:** `upload_iso37120_anexo`, `upload_iso37122_anexo`, `upload_iso37123_anexo`, `upload_iso37125_anexo` e todos os `delete_*_anexo`

---

### 1.3 — Remover credenciais hardcoded do settings.py

**Arquivo:** `datacity/settings.py`  
**Risco:** CRÍTICO — qualquer pessoa com acesso ao repo tem a senha do banco e a SECRET_KEY

**Problema:**
```python
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-k3x&07=...')  # fallback inseguro
'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'Rp123456'),                     # senha exposta
```

**Correção:**
```python
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']       # falha explicitamente se não definida
'PASSWORD': os.environ['DATABASE_PASSWORD'],        # sem fallback
```

**Ação adicional:** Verificar se o repositório já foi público com essas credenciais. Se sim, rotacionar a senha do banco e gerar nova SECRET_KEY imediatamente.

---

### 1.4 — `DEBUG = True` hardcoded

**Arquivo:** `datacity/settings.py`  
**Risco:** CRÍTICO — em produção com DEBUG=True, qualquer exceção expõe traceback completo com queries SQL, variáveis e paths do sistema

**Problema:**
```python
DEBUG = True  # hardcoded — nunca vai para False
```

**Correção:**
```python
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
```

---

### 1.5 — Configurações de produção contraditórias

**Arquivo:** `datacity/settings.py`  
**Risco:** ALTO — mesmo com DEBUG=False, cookies de sessão e CSRF trafegam em HTTP

**Problema:**
```python
if not DEBUG:
    SECURE_SSL_REDIRECT = False      # HTTPS desabilitado em prod!
    SESSION_COOKIE_SECURE = False    # cookie de sessão em HTTP!
    CSRF_COOKIE_SECURE = False       # csrf em HTTP!
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'http')  # 'http' errado!
```

**Correção:**
```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

---

### 1.6 — Remover `verify=False` no scraping

**Arquivo:** `scraping/services.py:25`  
**Risco:** ALTO — SSL verification desabilitado permite Man-in-the-Middle

**Problema:**
```python
response = requests.get(job.url, verify=False)
```

**Correção:**
```python
response = requests.get(job.url, timeout=30)  # verify=True é o padrão
```

---

### 1.7 — Corrigir redirect para URL inexistente nos decorators

**Arquivo:** `accounts/decorators.py`  
**Risco:** MÉDIO — `NoReverseMatch` em produção quando usuário sem permissão acessa página protegida

**Problema:**
```python
return redirect('home')  # 'home' não existe no urlconf
```

**Correção:**
```python
return redirect('menu')  # URL que existe
```

---

### 1.8 — Logout apenas via POST

**Arquivo:** `accounts/views.py:110`  
**Risco:** MÉDIO — logout via GET é vulnerável a CSRF logout attack

**Problema:**
```python
def logout(request):  # aceita GET — qualquer link pode fazer logout
    auth_logout(request)
```

**Correção:**
```python
@require_http_methods(["POST"])
def logout(request):
    auth_logout(request)
    return redirect('login')
```

---

### 1.9 — Remover `@csrf_exempt` dos endpoints de mutação

**Arquivo:** `accounts/views.py` — todas as funções `save_*`, `update_*`, `upload_*`, `delete_*`  
**Risco:** ALTO — CSRF protection completamente desativada para todas as mutations

**Problema:** `@csrf_exempt` foi adicionado para fazer os `fetch()` do JS funcionarem.  
**Solução correta:** incluir o token CSRF no header do fetch, não desabilitar a proteção.

**Correção no frontend (todos os fetch de mutação):**
```javascript
function getCsrfToken() {
    return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
}

fetch('/dashboard/api/iso37120/save/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify(data),
});
```

---

## FASE 2 — Reorganização do Settings
> **Prioridade: ALTA**  
> **Estimativa: 1 dia**  
> Pré-requisito para todas as fases seguintes.

---

### 2.1 — Separar settings por ambiente

**Situação atual:** Um único `settings.py` tenta servir dev e prod com `if not DEBUG:`.

**Nova estrutura:**
```
datacity/
└── settings/
    ├── __init__.py       # vazio
    ├── base.py           # configurações comuns a todos os ambientes
    ├── development.py    # DEBUG=True, console email, sem HTTPS
    └── production.py     # DEBUG=False, S3, Sentry, HTTPS obrigatório
```

**`base.py`** — contém: INSTALLED_APPS, AUTH_USER_MODEL, MIDDLEWARE, TEMPLATES, AUTH_PASSWORD_VALIDATORS, LANGUAGE_CODE, TIME_ZONE, STATIC/MEDIA URLs, LOGIN_URL, AUTHENTICATION_BACKENDS

**`development.py`** — contém:
```python
from .base import *

DEBUG = True
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-only-insecure-key')
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**`production.py`** — contém:
```python
from .base import *

DEBUG = False
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

**Atualizar `manage.py` e `wsgi.py`:**
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datacity.settings.development')
```

---

### 2.2 — Separar requirements por ambiente

**Nova estrutura:**
```
requirements/
├── base.txt         # Django, psycopg2, DRF, etc
├── development.txt  # -r base.txt + django-debug-toolbar, factory-boy
└── production.txt   # -r base.txt + sentry-sdk, gunicorn
```

---

### 2.3 — Configurar LOGGING no settings

**Arquivo:** `datacity/settings/base.py`

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'accounts': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'scraping': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
    },
}
```

---

### 2.4 — Adicionar DRF ao INSTALLED_APPS e configurar

**Arquivo:** `datacity/settings/base.py`

```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'corsheaders',
    'django_filters',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # deve ser o primeiro
    ...
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

---

### 2.5 — Remover side effects do settings.py

**Problema:**
```python
os.makedirs(os.path.join(BASE_DIR, 'static'), exist_ok=True)  # side effect!
```

**Correção:** Mover para `Dockerfile` ou script de deploy. Remover do settings.

---

## FASE 3 — Refatoração dos Models (Core Domain)
> **Prioridade: ALTA**  
> **Estimativa: 2-3 dias**  
> Esta é a mudança mais impactante — elimina 90% da duplicação do projeto.

---

### 3.1 — Unificar os 4 models ISO em 1

**Situação atual:** 4 models idênticos com 16 colunas de dado/fonte/anexo por ano = 64 colunas no total.

**Novo design:**

```python
# indicators/models.py

class ISOStandard(models.TextChoices):
    ISO37120 = 'ISO37120', 'ISO 37120'
    ISO37122 = 'ISO37122', 'ISO 37122'
    ISO37123 = 'ISO37123', 'ISO 37123'
    ISO37125 = 'ISO37125', 'ISO 37125'

class IndicatorType(models.TextChoices):
    CORE       = 'core',       'Principal'
    SUPPORTING = 'supporting', 'Apoio'
    PROFILE    = 'profile',    'Perfil'

class ISOIndicator(models.Model):
    standard       = models.CharField(max_length=10, choices=ISOStandard.choices)
    categoria      = models.CharField(max_length=100)
    nome_indicador = models.CharField(max_length=255)
    tipo           = models.CharField(max_length=20, choices=IndicatorType.choices)
    ods            = models.CharField(max_length=10)
    unidade        = models.CharField(max_length=50)
    cidade         = models.CharField(max_length=100)
    estado         = models.CharField(max_length=50)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['standard', 'nome_indicador', 'cidade', 'estado']
        indexes = [
            models.Index(fields=['standard', 'cidade', 'estado']),
        ]

class ISOIndicatorData(models.Model):
    indicator = models.ForeignKey(ISOIndicator, on_delete=models.CASCADE, related_name='data')
    year      = models.PositiveSmallIntegerField()
    dado      = models.CharField(max_length=100, null=True, blank=True)
    fonte     = models.CharField(max_length=500, null=True, blank=True)
    anexo     = models.FileField(upload_to='iso_indicators/anexos/%Y/', null=True, blank=True)

    class Meta:
        unique_together = ['indicator', 'year']
```

**Benefícios:**
- Adicionar ano 2026: 1 linha de código, 0 migrations de schema
- Adicionar ISO 37130: 1 linha no enum, 0 migrations de schema
- De 4 tables × ~20 colunas → 2 tables normalizadas
- De 20 view functions → 5 genéricas

**Migration de dados:** Criar data migration que lê as 4 tables antigas e popula as 2 novas.

---

### 3.2 — Criar Dimension e Indicator models reais (eliminar MOCK_DATA)

**Situação atual:** `MOCK_DATA` é um dict Python em memória — não persiste, não é thread-safe, não escala.

```python
# dashboard/models.py

class Dimension(models.Model):
    slug       = models.SlugField(max_length=50, unique=True)
    nome       = models.CharField(max_length=100)
    cor        = models.CharField(max_length=7)  # hex color
    ods        = models.CharField(max_length=50, blank=True)
    iso        = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

class Indicator(models.Model):
    dimension  = models.ForeignKey(Dimension, on_delete=models.CASCADE, related_name='indicators')
    nome       = models.CharField(max_length=255)
    dado       = models.CharField(max_length=255, blank=True)
    ods        = models.CharField(max_length=50, blank=True)
    fonte      = models.CharField(max_length=255, blank=True)
    iso        = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
```

**Criar data migration** para popular as dimensões com os dados que estavam no MOCK_DATA.

---

### 3.3 — Corrigir o model User

**Problemas a corrigir:**

```python
# ANTES
email = models.EmailField(unique=True, null=True, blank=True)  # nullable = bug
categoria = models.CharField(...)  # duplicado de user_type
Nome = models.CharField(...)        # PascalCase errado

# DEPOIS
email = models.EmailField(unique=True)             # obrigatório
nome  = models.CharField(max_length=100)           # snake_case
# categoria: REMOVER — user_type já serve o mesmo propósito
```

**Atenção:** Remover `categoria` exige:
1. Migration `RemoveField`
2. Atualizar todas as views que setam `categoria` e `user_type` juntos
3. Atualizar templates que exibem `categoria`

---

### 3.4 — Corrigir model Platform e Norm

**Problemas a corrigir:**

```python
# ANTES
class Platform(models.Model):
    id_plataforma = models.AutoField(primary_key=True)  # custom PK desnecessário
    Nome          = models.CharField(...)               # PascalCase
    Direcionamento = models.URLField()                  # PascalCase

# DEPOIS
class Platform(models.Model):
    # id automático do Django (BigAutoField via DEFAULT_AUTO_FIELD)
    nome = models.CharField(max_length=100, unique=True)
    url  = models.URLField()

    class Meta:
        ordering = ['nome']
        verbose_name = 'Plataforma'
        verbose_name_plural = 'Plataformas'
```

**Mesma correção para `Norm`.**

---

## FASE 4 — Separação Arquitetural (Criação dos Apps)
> **Prioridade: ALTA**  
> **Estimativa: 3-5 dias**  
> Pré-requisito: Fase 3 concluída.

---

### 4.1 — Nova estrutura de diretórios

```
datacity-project/
├── apps/
│   ├── __init__.py
│   ├── authentication/     # User model, login, logout
│   ├── users/              # Gerenciamento de usuários (admin)
│   ├── indicators/         # ISO indicators — domínio central
│   ├── platforms/          # Plataformas externas
│   ├── norms/              # Normas
│   ├── dashboard/          # Views de dashboard, Dimension, Indicator
│   └── scraping/           # Web scraping (mover de scraping/)
├── config/                 # Renomear datacity/ para config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── templates/
├── static/
├── media/
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── manage.py
├── .env.example
├── docker-compose.yml
└── Dockerfile
```

---

### 4.2 — App: `authentication`

**Responsabilidade:** Apenas autenticação — User model, login, logout, register, backends.

**Arquivos:**
```
apps/authentication/
├── models.py      # User (AbstractUser)
├── views.py       # login, logout, register
├── forms.py       # LoginForm, RegisterForm
├── backends.py    # EmailBackend
├── urls.py
└── apps.py
```

**Regra:** Nenhum outro domínio deve estar aqui. Se não é sobre "quem é o usuário", não pertence.

---

### 4.3 — App: `users`

**Responsabilidade:** CRUD de usuários pelo administrador do sistema.

**Arquivos:**
```
apps/users/
├── views.py       # list_users, add_user, edit_user, delete_user, change_user_role
├── serializers.py # UserSerializer (DRF)
├── permissions.py # IsAdmin
├── urls.py
└── apps.py
```

**Observação:** Não tem `models.py` próprio — importa `User` de `authentication`.

---

### 4.4 — App: `indicators`

**Responsabilidade:** Gestão de indicadores ISO 37120/37122/37123/37125. É o domínio central.

**Arquivos:**
```
apps/indicators/
├── models.py      # ISOIndicator, ISOIndicatorData
├── serializers.py # ISOIndicatorSerializer, ISOIndicatorDataSerializer
├── views.py       # ISOIndicatorViewSet (DRF ViewSet)
├── services.py    # ISOIndicatorService (lógica de negócio)
├── permissions.py # IsManagerOrReadOnly
├── filters.py     # ISOIndicatorFilter
├── urls.py
└── apps.py
```

**Serviço:**
```python
# apps/indicators/services.py

class ISOIndicatorService:
    @staticmethod
    def save_indicator(standard, nome_indicador, cidade, estado, fields: dict) -> ISOIndicator:
        ...

    @staticmethod
    def upload_attachment(indicator_id: int, year: int, file) -> str:
        ...

    @staticmethod
    def delete_attachment(indicator_id: int, year: int) -> None:
        ...
```

---

### 4.5 — App: `platforms`

**Responsabilidade:** Plataformas externas (link externo com nome).

**Arquivos:**
```
apps/platforms/
├── models.py      # Platform
├── serializers.py # PlatformSerializer
├── views.py       # PlatformViewSet
├── permissions.py # IsAdminOrReadOnly
├── urls.py
└── apps.py
```

---

### 4.6 — App: `norms`

**Responsabilidade:** Normas e padrões (link externo com nome).

**Arquivos:**
```
apps/norms/
├── models.py      # Norm
├── serializers.py # NormSerializer
├── views.py       # NormViewSet
├── permissions.py # IsAdminOrReadOnly
├── urls.py
└── apps.py
```

---

### 4.7 — App: `dashboard`

**Responsabilidade:** Views HTML do dashboard (não é API). Contém Dimension e Indicator mock→real.

**Arquivos:**
```
apps/dashboard/
├── models.py      # Dimension, Indicator
├── views.py       # menu, dimensoes, indicadores, gerar_relatorio
├── serializers.py # DimensionSerializer, IndicatorSerializer
├── urls.py
└── apps.py
```

---

### 4.8 — Reorganização das URLs

**`config/urls.py`:**
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.authentication.urls')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('api/v1/', include('apps.api_router.urls', namespace='api')),
]
```

**`apps/api_router/urls.py`:**
```python
router = DefaultRouter()
router.register(r'indicators', ISOIndicatorViewSet, basename='indicator')
router.register(r'platforms', PlatformViewSet, basename='platform')
router.register(r'norms', NormViewSet, basename='norm')
router.register(r'users', UserViewSet, basename='user')
router.register(r'scraping/jobs', ScrapingJobViewSet, basename='scraping-job')

urlpatterns = router.urls
```

---

## FASE 5 — Implementação DRF (APIs Corretas)
> **Prioridade: MÉDIA-ALTA**  
> **Estimativa: 3-4 dias**  
> Pré-requisito: Fase 4 concluída.

---

### 5.1 — Serializers para cada domínio

```python
# apps/indicators/serializers.py

class ISOIndicatorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISOIndicatorData
        fields = ['id', 'year', 'dado', 'fonte', 'anexo']

class ISOIndicatorSerializer(serializers.ModelSerializer):
    data = ISOIndicatorDataSerializer(many=True, read_only=True)

    class Meta:
        model = ISOIndicator
        fields = ['id', 'standard', 'categoria', 'nome_indicador', 'tipo',
                  'ods', 'unidade', 'cidade', 'estado', 'data',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
```

---

### 5.2 — ViewSets com permissões corretas

```python
# apps/indicators/views.py

class ISOIndicatorViewSet(ModelViewSet):
    serializer_class   = ISOIndicatorSerializer
    permission_classes = [IsAuthenticated, IsManagerOrReadOnly]
    filterset_class    = ISOIndicatorFilter
    search_fields      = ['nome_indicador', 'categoria']
    ordering_fields    = ['categoria', 'nome_indicador', 'created_at']

    def get_queryset(self):
        return (
            ISOIndicator.objects
            .prefetch_related('data')
            .filter(
                cidade=self.request.query_params.get('cidade', 'Londrina'),
                estado=self.request.query_params.get('estado', 'PR'),
            )
        )
```

---

### 5.3 — Permissions customizadas

```python
# apps/indicators/permissions.py

class IsManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and (
            request.user.is_admin() or request.user.is_manager()
        )
```

---

### 5.4 — Endpoint de upload de anexo como action

```python
# apps/indicators/views.py

class ISOIndicatorViewSet(ModelViewSet):
    ...

    @action(detail=True, methods=['post'], url_path='data/(?P<year>[0-9]{4})/anexo')
    def upload_anexo(self, request, pk=None, year=None):
        if int(year) not in {2022, 2023, 2024, 2025}:
            return Response({'error': 'Ano inválido'}, status=400)

        indicator = self.get_object()
        file = request.FILES.get('anexo')

        if not file:
            return Response({'error': 'Arquivo não enviado'}, status=400)

        if not file.name.lower().endswith('.pdf'):
            return Response({'error': 'Apenas PDF é permitido'}, status=400)

        if file.size > 10 * 1024 * 1024:
            return Response({'error': 'Arquivo maior que 10MB'}, status=400)

        url = ISOIndicatorService.upload_attachment(indicator.id, int(year), file)
        return Response({'url': url})
```

---

### 5.5 — Filtros com django-filter

```python
# apps/indicators/filters.py

class ISOIndicatorFilter(FilterSet):
    standard  = CharFilter(field_name='standard', lookup_expr='exact')
    cidade    = CharFilter(field_name='cidade',   lookup_expr='iexact')
    estado    = CharFilter(field_name='estado',   lookup_expr='iexact')
    categoria = CharFilter(field_name='categoria', lookup_expr='icontains')

    class Meta:
        model = ISOIndicator
        fields = ['standard', 'cidade', 'estado', 'categoria', 'tipo']
```

---

## FASE 6 — Testes
> **Prioridade: ALTA** (sem testes, nenhuma refatoração é segura)  
> **Estimativa: 3-5 dias** (ongoing)  
> Deve começar junto com a Fase 3 para proteger as mudanças.

---

### 6.1 — Configurar ambiente de testes

```python
# requirements/development.txt
factory-boy==3.3.0
pytest-django==4.7.0
pytest-cov==4.1.0
model-bakery==1.17.0
```

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = tests/test_*.py
addopts = --cov=apps --cov-report=term-missing
```

---

### 6.2 — Factories

```python
# tests/factories.py

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username   = factory.Sequence(lambda n: f'user_{n}')
    email      = factory.LazyAttribute(lambda o: f'{o.username}@test.com')
    user_type  = User.UserType.COMMON

class AdminUserFactory(UserFactory):
    user_type = User.UserType.ADMIN

class ISOIndicatorFactory(DjangoModelFactory):
    class Meta:
        model = ISOIndicator

    standard       = ISOStandard.ISO37120
    categoria      = 'Economia'
    nome_indicador = factory.Sequence(lambda n: f'Indicador {n}')
    tipo           = IndicatorType.CORE
    cidade         = 'Londrina'
    estado         = 'PR'
```

---

### 6.3 — Testes de segurança (prioridade máxima)

```python
# tests/test_security.py

class TestSetAttrWhitelist:
    def test_rejects_non_whitelisted_field(self, manager_client, indicator):
        response = manager_client.post('/api/v1/indicators/1/update_field/', {
            'field_name': 'cidade',
            'field_value': 'São Paulo'
        })
        assert response.status_code == 400

    def test_rejects_id_field(self, manager_client, indicator):
        response = manager_client.post('/api/v1/indicators/1/update_field/', {
            'field_name': 'id',
            'field_value': 999
        })
        assert response.status_code == 400

class TestYearValidation:
    def test_rejects_invalid_year(self, manager_client):
        response = manager_client.post('/api/v1/indicators/1/data/2099/anexo', ...)
        assert response.status_code == 400

    def test_rejects_non_numeric_year(self, manager_client):
        response = manager_client.post('/api/v1/indicators/1/data/__class__/anexo', ...)
        assert response.status_code == 404  # URL regex não casa

class TestPermissions:
    def test_common_user_cannot_save_indicator(self, common_client):
        response = common_client.post('/api/v1/indicators/', {...})
        assert response.status_code == 403

    def test_anonymous_cannot_access_api(self, client):
        response = client.get('/api/v1/indicators/')
        assert response.status_code == 401
```

---

### 6.4 — Testes de services

```python
# tests/test_indicator_service.py

class TestISOIndicatorService:
    def test_save_creates_new_indicator(self, db):
        indicator = ISOIndicatorService.save_indicator(
            standard='ISO37120',
            nome_indicador='Taxa de alfabetização',
            cidade='Londrina',
            estado='PR',
            fields={'categoria': 'Educação', 'tipo': 'core'}
        )
        assert ISOIndicator.objects.count() == 1
        assert indicator.nome_indicador == 'Taxa de alfabetização'

    def test_save_updates_existing_indicator(self, db, indicator):
        ISOIndicatorService.save_indicator(
            standard=indicator.standard,
            nome_indicador=indicator.nome_indicador,
            cidade=indicator.cidade,
            estado=indicator.estado,
            fields={'categoria': 'Nova Categoria'}
        )
        indicator.refresh_from_db()
        assert indicator.categoria == 'Nova Categoria'
        assert ISOIndicator.objects.count() == 1  # não criou duplicata
```

---

### 6.5 — Testes de API (integração)

```python
# tests/test_indicators_api.py

class TestISOIndicatorAPI:
    def test_list_returns_only_city_data(self, auth_client, db):
        ISOIndicatorFactory(cidade='Londrina', estado='PR')
        ISOIndicatorFactory(cidade='Curitiba', estado='PR')

        response = auth_client.get('/api/v1/indicators/?cidade=Londrina')
        assert response.status_code == 200
        assert len(response.data['results']) == 1

    def test_list_is_paginated(self, auth_client, db):
        ISOIndicatorFactory.create_batch(100)
        response = auth_client.get('/api/v1/indicators/')
        assert 'next' in response.data
        assert len(response.data['results']) == 50  # PAGE_SIZE
```

---

## FASE 7 — Performance e Infraestrutura
> **Prioridade: MÉDIA**  
> **Estimativa: 2-3 dias**  
> Fazer após a arquitetura estar estável.

---

### 7.1 — Cache com Redis

```python
# config/settings/production.py

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ['REDIS_URL'],
    }
}

# apps/platforms/views.py — exemplo de uso
from django.core.cache import cache

class PlatformViewSet(ReadOnlyModelViewSet):
    def list(self, request):
        data = cache.get('platforms_list')
        if not data:
            data = super().list(request).data
            cache.set('platforms_list', data, timeout=300)
        return Response(data)
```

---

### 7.2 — Scraping assíncrono com Celery

```python
# apps/scraping/tasks.py

from celery import shared_task

@shared_task(bind=True, max_retries=3)
def execute_scraping_job(self, job_id: int):
    try:
        ScrapingService.execute_job(job_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

# apps/scraping/views.py — retorna imediatamente
class ScrapingJobViewSet(ModelViewSet):
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        job = self.get_object()
        execute_scraping_job.delay(job.id)  # assíncrono
        return Response({'status': 'queued', 'job_id': job.id})
```

```python
# config/settings/base.py
CELERY_BROKER_URL  = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
```

---

### 7.3 — Paginação nas queries existentes

Todas as views que listam indicadores devem paginar.  
Com DRF, isso é automático via `DEFAULT_PAGINATION_CLASS` no settings.  
Verificar que nenhuma query retorna querysets unbounded.

---

### 7.4 — `select_related` e `prefetch_related`

```python
# SEMPRE que buscar indicators com data relacionada:
ISOIndicator.objects.prefetch_related('data').filter(...)

# SEMPRE que buscar users com dados relacionados:
User.objects.select_related(...).all()
```

Adicionar `indexes` nos campos de filtro mais comuns:
```python
class Meta:
    indexes = [
        models.Index(fields=['standard', 'cidade', 'estado']),
        models.Index(fields=['cidade', 'estado']),
    ]
```

---

### 7.5 — Remover a view `serve_static`

**Arquivo:** `accounts/views.py:1703`, `accounts/urls.py:42`

Django não deve servir static files em produção. Configurar Nginx ou WhiteNoise:

```python
# requirements/production.txt
whitenoise==6.6.0

# config/settings/production.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # logo após security
    ...
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

Remover:
- `path('static/<path:path>', views.serve_static)` das URLs
- A função `serve_static` do views.py

---

## FASE 8 — Qualidade de Código
> **Prioridade: MÉDIA**  
> **Estimativa: 1-2 dias**  
> Pode ser feita em paralelo com outras fases.

---

### 8.1 — Type hints em todo o código novo

```python
# Todo código novo deve ter type hints
from django.http import HttpRequest, JsonResponse
from typing import Any

def save_indicator(request: HttpRequest) -> JsonResponse:
    ...
```

---

### 8.2 — Context processor para dados do usuário

Remover de todas as views:
```python
# REMOVER de cada view — repetido em ~20 lugares
context = {
    'username': request.user.username,
    'user_type': request.user.user_type,
}
```

Criar:
```python
# apps/authentication/context_processors.py
def user_context(request: HttpRequest) -> dict[str, Any]:
    if request.user.is_authenticated:
        return {
            'current_user': request.user,
            'user_type': request.user.user_type,
        }
    return {}

# config/settings/base.py — adicionar em TEMPLATES.OPTIONS.context_processors
'apps.authentication.context_processors.user_context',
```

---

### 8.3 — Extrair constantes para arquivo dedicado

```python
# apps/indicators/constants.py

DEFAULT_CITY  = 'Londrina'
DEFAULT_STATE = 'PR'
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB
VALID_YEARS   = frozenset({2022, 2023, 2024, 2025})
ALLOWED_ATTACHMENT_EXTENSIONS = frozenset({'.pdf'})
```

---

### 8.4 — Remover código morto

- Função `index` em `views.py` (dead code — não está nas URLs)
- URL de `dashboard/` apontando para `views.menu` com `name='index'` (duplicata de `menu`)
- `import json` dentro de funções (já importado no topo)
- Registro de cadastro comentado nas URLs

---

### 8.5 — Linter e formatter

```
# pyproject.toml
[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
plugins = ["mypy_django_plugin.main"]
```

---

## FASE 9 — Bootstrap (Frontend Consistente)
> **Prioridade: MÉDIA**  
> **Estimativa: 2-3 dias**  
> Pode ser feita em paralelo com a Fase 4. Pré-requisito: existir uma estrutura de templates organizada.

---

### Diagnóstico atual

O projeto tem **dois problemas distintos** com Bootstrap:

1. **Bootstrap via CDN externo** — `base.html` carrega do `cdn.jsdelivr.net`. Em produção sem internet ou com CDN fora, o layout quebra inteiramente.
2. **Templates não herdam nenhuma base** — os ~25 templates dentro de `accounts/templates/` são HTML completo autônomo com CSS inline. Nenhum faz `{% extends %}`. Resultado: qualquer mudança de layout exige editar 25+ arquivos.

```
templates/
├── base.html              ← Bootstrap via CDN, mas NINGUÉM herda isso
├── landing.html           ← standalone
└── saiba_mais.html        ← standalone

accounts/templates/
├── accounts/login.html    ← standalone, sem Bootstrap, CSS inline de 200+ linhas
├── new-screens/menu.html  ← standalone, CSS inline de 300+ linhas
├── new-screens/iso37120.html
└── ...                    ← todos standalone
```

---

### 9.1 — Instalar Bootstrap localmente (remover dependência de CDN)

**Por que CDN é problemático em produção:**
- Falha se o servidor não tiver acesso à internet
- Viola CSP (Content Security Policy) estrita
- A versão pode mudar sem aviso (`bootstrap@5.3.0` no CDN pode ser removida)
- Adiciona latência de DNS externo em cada carregamento

**Opção A — Via npm (recomendado se o projeto já usa ou vai usar JS build):**
```bash
npm init -y
npm install bootstrap@5.3.3
```

```javascript
// static/js/main.js
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
```

**Opção B — Via pip com django-bootstrap5 (mais simples, sem Node):**
```bash
pip install django-bootstrap5==24.3
```

```python
# config/settings/base.py
INSTALLED_APPS = [
    ...
    'django_bootstrap5',
]
```

**Opção C — Download direto dos arquivos (mais simples, sem dependências extras):**
```
static/
├── css/
│   └── bootstrap.min.css    # download de bootstrap.com
├── js/
│   └── bootstrap.bundle.min.js
└── img/
```

> **Recomendação para este projeto:** Opção C no curto prazo (velocidade), migrar para Opção A quando houver um pipeline de build JS.

---

### 9.2 — Criar hierarquia de templates com herança real

**Estrutura proposta:**

```
templates/
├── base.html                  # base global — Bootstrap, meta tags, navbar, footer
├── base_dashboard.html        # herda base.html — adiciona sidebar, breadcrumb
├── base_auth.html             # herda base.html — layout centralizado (login/register)
│
├── authentication/
│   ├── login.html             # herda base_auth.html
│   └── register.html          # herda base_auth.html
│
├── dashboard/
│   ├── menu.html              # herda base_dashboard.html
│   ├── dimensoes.html         # herda base_dashboard.html
│   └── indicadores.html       # herda base_dashboard.html
│
├── indicators/
│   ├── iso37120.html          # herda base_dashboard.html
│   ├── iso37122.html          # herda base_dashboard.html
│   ├── iso37123.html          # herda base_dashboard.html
│   └── iso37125.html          # herda base_dashboard.html
│
├── platforms/
│   └── plataformas.html       # herda base_dashboard.html
│
├── norms/
│   └── normas.html            # herda base_dashboard.html
│
├── users/
│   ├── list_users.html        # herda base_dashboard.html
│   ├── add_user.html          # herda base_dashboard.html
│   └── edit_user.html         # herda base_dashboard.html
│
└── landing.html               # herda base.html (página pública)
```

---

### 9.3 — Conteúdo do `base.html` corrigido

```html
{# templates/base.html #}
{% load static %}
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{% block meta_description %}DataCity — Plataforma de Dados Urbanos{% endblock %}">
    <title>{% block title %}DataCity{% endblock %} — DataCity</title>

    {# Bootstrap LOCAL — sem CDN externo #}
    <link rel="stylesheet" href="{% static 'css/bootstrap.min.css' %}">
    {# Ícones Bootstrap #}
    <link rel="stylesheet" href="{% static 'css/bootstrap-icons.min.css' %}">
    {# CSS customizado do projeto #}
    <link rel="stylesheet" href="{% static 'css/main.css' %}">

    {% block extra_css %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">

    {% block navbar %}
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand fw-bold" href="{% url 'landing' %}">DataCity</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarMain">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarMain">
                {% if user.is_authenticated %}
                <ul class="navbar-nav ms-auto align-items-center gap-2">
                    <li class="nav-item">
                        <span class="nav-link text-light">
                            <i class="bi bi-person-circle"></i>
                            {{ user.nome|default:user.username }}
                            <span class="badge bg-secondary ms-1">{{ user.get_user_type_display }}</span>
                        </span>
                    </li>
                    <li class="nav-item">
                        <form method="post" action="{% url 'logout' %}" class="d-inline">
                            {% csrf_token %}
                            <button type="submit" class="btn btn-sm btn-outline-light">Sair</button>
                        </form>
                    </li>
                </ul>
                {% endif %}
            </div>
        </div>
    </nav>
    {% endblock %}

    {# Mensagens do Django (success, error, warning) #}
    {% if messages %}
    <div class="container mt-2">
        {% for message in messages %}
        <div class="alert alert-{% if message.tags == 'error' %}danger{% else %}{{ message.tags }}{% endif %} alert-dismissible fade show" role="alert">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <main class="{% block main_class %}{% endblock %}">
        {% block content %}{% endblock %}
    </main>

    {% block footer %}{% endblock %}

    {# Bootstrap JS LOCAL #}
    <script src="{% static 'js/bootstrap.bundle.min.js' %}"></script>
    {# JS customizado do projeto #}
    <script src="{% static 'js/main.js' %}"></script>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

---

### 9.4 — `base_dashboard.html` com sidebar

```html
{# templates/base_dashboard.html #}
{% extends "base.html" %}
{% load static %}

{% block body_class %}bg-light{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">

        {# Sidebar #}
        <nav class="col-md-2 d-md-block bg-dark sidebar collapse py-3" style="min-height: calc(100vh - 56px)">
            <ul class="nav flex-column">
                <li class="nav-item">
                    <a class="nav-link text-white {% block nav_menu %}{% endblock %}" href="{% url 'dashboard:menu' %}">
                        <i class="bi bi-house-door me-2"></i>Início
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link text-white-50 {% block nav_dimensoes %}{% endblock %}" href="{% url 'dashboard:dimensoes' %}">
                        <i class="bi bi-grid me-2"></i>Dimensões
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link text-white-50" href="{% url 'norms:list' %}">
                        <i class="bi bi-file-text me-2"></i>Normas
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link text-white-50" href="{% url 'platforms:list' %}">
                        <i class="bi bi-link-45deg me-2"></i>Plataformas
                    </a>
                </li>
                {% if user.is_admin %}
                <li class="nav-item mt-3">
                    <span class="nav-link text-secondary small text-uppercase">Administração</span>
                </li>
                <li class="nav-item">
                    <a class="nav-link text-white-50" href="{% url 'users:list' %}">
                        <i class="bi bi-people me-2"></i>Usuários
                    </a>
                </li>
                {% endif %}
            </ul>
        </nav>

        {# Conteúdo principal #}
        <main class="col-md-10 ms-sm-auto px-md-4 py-3">
            {% block breadcrumb %}{% endblock %}
            {% block dashboard_content %}{% endblock %}
        </main>

    </div>
</div>
{% endblock %}
```

---

### 9.5 — `base_auth.html` para login/register

```html
{# templates/base_auth.html #}
{% extends "base.html" %}
{% load static %}

{% block navbar %}{% endblock %}{# sem navbar nas páginas de auth #}
{% block body_class %}bg-dark{% endblock %}

{% block content %}
<div class="min-vh-100 d-flex align-items-center justify-content-center">
    <div class="col-md-4 col-lg-3">
        <div class="text-center mb-4">
            <h1 class="text-white fw-bold">DataCity</h1>
            <p class="text-white-50">{% block auth_subtitle %}{% endblock %}</p>
        </div>
        <div class="card shadow-lg border-0">
            <div class="card-body p-4">
                {% block auth_content %}{% endblock %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

### 9.6 — Exemplo: login.html migrado para herança

```html
{# templates/authentication/login.html #}
{% extends "base_auth.html" %}
{% load static %}

{% block title %}Login{% endblock %}
{% block auth_subtitle %}Acesse sua conta{% endblock %}

{% block auth_content %}
<h5 class="card-title mb-4 fw-semibold">Entrar</h5>

<form method="post" action="{% url 'login' %}">
    {% csrf_token %}

    <div class="mb-3">
        <label for="id_username" class="form-label">Email ou Usuário</label>
        <input type="text"
               id="id_username"
               name="username"
               class="form-control {% if form.username.errors %}is-invalid{% endif %}"
               placeholder="seu@email.com"
               autocomplete="username"
               required>
        {% for error in form.username.errors %}
            <div class="invalid-feedback">{{ error }}</div>
        {% endfor %}
    </div>

    <div class="mb-4">
        <label for="id_password" class="form-label">Senha</label>
        <input type="password"
               id="id_password"
               name="password"
               class="form-control {% if form.password.errors %}is-invalid{% endif %}"
               placeholder="••••••••"
               autocomplete="current-password"
               required>
        {% for error in form.password.errors %}
            <div class="invalid-feedback">{{ error }}</div>
        {% endfor %}
    </div>

    <button type="submit" class="btn btn-primary w-100">
        <i class="bi bi-box-arrow-in-right me-2"></i>Entrar
    </button>
</form>
{% endblock %}
```

---

### 9.7 — CSS customizado mínimo

```css
/* static/css/main.css */

/* Variáveis do tema DataCity */
:root {
    --datacity-primary: #0d6efd;
    --datacity-sidebar-bg: #212529;
    --datacity-sidebar-width: 16.666667%; /* col-md-2 */
}

/* Sidebar fixa em telas grandes */
@media (min-width: 768px) {
    .sidebar {
        position: sticky;
        top: 56px; /* altura da navbar */
        height: calc(100vh - 56px);
        overflow-y: auto;
    }
}

/* Transição suave nos links de nav */
.nav-link {
    transition: color 0.15s ease, background-color 0.15s ease;
    border-radius: 0.375rem;
}

.nav-link:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

/* Cards de indicadores ISO */
.indicator-card {
    transition: box-shadow 0.2s ease;
}

.indicator-card:hover {
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
}
```

---

### 9.8 — Componente de mensagens reutilizável

```html
{# templates/components/messages.html #}
{% if messages %}
<div class="messages-container">
    {% for message in messages %}
    <div class="alert alert-{% if message.tags == 'error' %}danger{% elif message.tags == 'debug' %}secondary{% else %}{{ message.tags }}{% endif %} alert-dismissible fade show"
         role="alert">
        {% if message.tags == 'success' %}<i class="bi bi-check-circle me-2"></i>{% endif %}
        {% if message.tags == 'error' %}<i class="bi bi-exclamation-triangle me-2"></i>{% endif %}
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
    </div>
    {% endfor %}
</div>
{% endif %}
```

Usar em `base.html`:
```html
{% include "components/messages.html" %}
```

---

### 9.9 — Pontos de atenção na migração dos templates

- **Auditar CSS inline**: cada template tem 100-300 linhas de CSS inline. Extrair o que é reaproveitável para `main.css`, descartar o que Bootstrap já resolve.
- **Não duplicar Bootstrap**: verificar que nenhum template migrado ainda carrega Bootstrap por CDN depois de herdar `base.html`.
- **Manter os templates antigos funcionando** até que o novo esteja validado — usar feature flag de template se necessário.
- **Bootstrap Icons**: adicionar `bootstrap-icons` para ícones consistentes (substitui qualquer CDN de FontAwesome que possa existir nos templates antigos).

---

## FASE 10 — Docker
> **Prioridade: ALTA** (necessário para ambiente reproduzível de dev e deploy)  
> **Estimativa: 1-2 dias**  
> Pode ser feita em paralelo com a Fase 2 (settings). Nenhuma dependência de outras fases.

---

### 10.1 — Estrutura de arquivos Docker

```
datacity-project/
├── Dockerfile
├── docker-compose.yml          # ambiente de desenvolvimento
├── docker-compose.prod.yml     # overrides de produção
├── .dockerignore
├── .env.example                # template de variáveis (sem valores reais)
└── .env                        # valores reais (no .gitignore!)
```

---

### 10.2 — Dockerfile (multi-stage)

```dockerfile
# Dockerfile

# ─── Stage 1: builder ───────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Dependências de sistema para psycopg2 e lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python em camada separada (cache de layer)
COPY requirements/base.txt requirements/base.txt
COPY requirements/production.txt requirements/production.txt
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements/production.txt


# ─── Stage 2: runner ────────────────────────────────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

# Dependências de runtime apenas
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Instala wheels do stage anterior (sem compilação)
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*

# Cria usuário não-root para segurança
RUN addgroup --system datacity && adduser --system --group datacity

# Copia o código
COPY --chown=datacity:datacity . .

# Cria diretórios necessários
RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chown -R datacity:datacity /app/staticfiles /app/media /app/logs

USER datacity

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

CMD ["gunicorn", "config.wsgi:application", "--config", "gunicorn_config.py"]
```

**Por que multi-stage:**
- Stage `builder` tem gcc e libs de compilação (necessários para instalar psycopg2 etc.)
- Stage `runner` não tem compilador — imagem final ~60% menor
- Menor surface de ataque (sem ferramentas de build em produção)

---

### 10.3 — `docker-compose.yml` (desenvolvimento)

```yaml
# docker-compose.yml
version: '3.9'

services:

  web:
    build:
      context: .
      target: builder  # usa o stage builder em dev (tem mais ferramentas)
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             python manage.py runserver 0.0.0.0:8000"
    volumes:
      - .:/app                        # hot reload: código local montado no container
      - media_data:/app/media
    ports:
      - "8000:8000"
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.development
      DJANGO_DEBUG: "True"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: ${DATABASE_NAME:-datacity}
      POSTGRES_USER: ${DATABASE_USER:-datacity_user}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
    ports:
      - "5432:5432"                   # exposto apenas em dev
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DATABASE_USER:-datacity_user}"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"                   # exposto apenas em dev
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  celery:
    build:
      context: .
      target: builder
    command: celery -A config worker --loglevel=info --concurrency=2
    volumes:
      - .:/app
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.development
    env_file:
      - .env
    depends_on:
      - redis
      - db
    restart: unless-stopped

  celery-beat:
    build:
      context: .
      target: builder
    command: celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - .:/app
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.development
    env_file:
      - .env
    depends_on:
      - redis
      - db
    restart: unless-stopped

volumes:
  postgres_data:
  media_data:
```

---

### 10.4 — `docker-compose.prod.yml` (overrides de produção)

```yaml
# docker-compose.prod.yml
# Usar com: docker-compose -f docker-compose.yml -f docker-compose.prod.yml up

version: '3.9'

services:

  web:
    build:
      target: runner          # imagem de produção — menor, sem compilador
    command: >
      sh -c "python manage.py migrate --noinput &&
             python manage.py collectstatic --noinput &&
             gunicorn config.wsgi:application --config gunicorn_config.py"
    volumes:
      - media_data:/app/media
      - static_data:/app/staticfiles
      # SEM volume de código — imagem é self-contained em prod
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.production
      DJANGO_DEBUG: "False"
    ports:
      - "8000:8000"
    restart: always

  nginx:
    image: nginx:1.25-alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static_data:/var/www/static:ro
      - media_data:/var/www/media:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    restart: always

  db:
    ports: []                 # sem porta exposta em produção
    restart: always

  redis:
    ports: []                 # sem porta exposta em produção
    restart: always

  celery:
    build:
      target: runner
    command: celery -A config worker --loglevel=warning --concurrency=4
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.production
    restart: always

volumes:
  static_data:
```

---

### 10.5 — `nginx/nginx.conf`

```nginx
# nginx/nginx.conf

upstream datacity_app {
    server web:8000;
}

server {
    listen 80;
    server_name datacity.unifil.tech;

    # Redireciona todo HTTP para HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name datacity.unifil.tech;

    ssl_certificate     /etc/ssl/certs/datacity.crt;
    ssl_certificate_key /etc/ssl/private/datacity.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options       DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection      "1; mode=block";
    add_header Referrer-Policy       "strict-origin-when-cross-origin";

    client_max_body_size 15M;        # maior que o limite de 10MB dos anexos

    # Static files servidos diretamente pelo Nginx (não passa pelo Django)
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media files
    location /media/ {
        alias /var/www/media/;
        expires 1M;
        add_header Cache-Control "public";
        access_log off;
    }

    # Tudo mais vai para o Django
    location / {
        proxy_pass         http://datacity_app;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
    }
}
```

---

### 10.6 — `.dockerignore`

```
# .dockerignore

# Git
.git
.gitignore

# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage

# Ambiente virtual
venv/
.venv/
env/

# Dados locais
*.sqlite3
db.sqlite3

# Media e static coletado (gerados no build)
media/
staticfiles/

# Ambiente
.env
.env.*
!.env.example

# Logs
logs/
*.log

# Documentação e planos
*.md
docs/

# IDE
.vscode/
.idea/
*.swp

# Node (se existir)
node_modules/
npm-debug.log

# Scripts utilitários que não vão para prod
migrate_to_postgres.py
test_db_connection.py
test_api.py
powerbi_scraper.py
```

---

### 10.7 — `.env.example`

```bash
# .env.example
# Copie para .env e preencha com os valores reais
# NUNCA commite o .env no repositório

# Django
DJANGO_SECRET_KEY=gerar-com-python-secrets-token-hex-50
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de dados
DATABASE_NAME=datacity
DATABASE_USER=datacity_user
DATABASE_PASSWORD=PREENCHER
DATABASE_HOST=db
DATABASE_PORT=5432

# Redis / Celery
REDIS_URL=redis://redis:6379/0

# Email (produção)
EMAIL_HOST=smtp.seuservidor.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@datacity.com
EMAIL_HOST_PASSWORD=PREENCHER
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=DataCity <noreply@datacity.com>

# Storage (produção — S3 ou compatível)
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_STORAGE_BUCKET_NAME=
# AWS_S3_REGION_NAME=
```

---

### 10.8 — `gunicorn_config.py` revisado

```python
# gunicorn_config.py
import multiprocessing
import os

# Binding
bind = "0.0.0.0:8000"

# Workers — fórmula padrão: (2 × CPUs) + 1
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"           # usar "gevent" se adicionar gevent no requirements
worker_connections = 1000
timeout = 30                    # kill worker se não responder em 30s
keepalive = 5

# Graceful reload
max_requests = 1000             # restart worker após N requests (evita memory leak)
max_requests_jitter = 100       # jitter para evitar restart simultâneo de todos

# Logging
accesslog = "-"                 # stdout → coletado pelo Docker
errorlog  = "-"                 # stderr → coletado pelo Docker
loglevel  = os.environ.get('GUNICORN_LOG_LEVEL', 'warning')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)sµs'

# Segurança
forwarded_allow_ips = "*"       # confia no X-Forwarded-For do Nginx
proxy_protocol = False
```

---

### 10.9 — Comandos de desenvolvimento com Docker

```bash
# Subir ambiente completo
docker-compose up

# Subir em background
docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f web
docker-compose logs -f celery

# Rodar migrations
docker-compose exec web python manage.py migrate

# Criar superuser
docker-compose exec web python manage.py createsuperuser

# Abrir shell Django
docker-compose exec web python manage.py shell

# Abrir psql diretamente
docker-compose exec db psql -U datacity_user -d datacity

# Rodar testes
docker-compose exec web pytest

# Parar tudo
docker-compose down

# Parar e remover volumes (CUIDADO — apaga banco)
docker-compose down -v

# Deploy em produção
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

### 10.10 — Health check endpoint no Django

O Dockerfile referencia `/health/`. Criar:

```python
# config/urls.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('health/', health_check, name='health_check'),
    ...
]
```

---

## Checklist de Execução

### Fase 1 — Segurança (BLOQUEANTE)
- [ ] 1.1 Whitelist no `setattr` (4 funções update_field)
- [ ] 1.2 Validação de `year` (8 funções de anexo)
- [ ] 1.3 Remover credenciais hardcoded do settings.py
- [ ] 1.4 `DEBUG = os.environ.get(...)`
- [ ] 1.5 Corrigir configurações de produção (SSL, cookies)
- [ ] 1.6 Remover `verify=False` do scraping
- [ ] 1.7 Corrigir redirect `'home'` → `'menu'` nos decorators
- [ ] 1.8 Logout apenas via POST
- [ ] 1.9 Remover `@csrf_exempt` + adicionar X-CSRFToken no frontend

### Fase 2 — Settings
- [ ] 2.1 Separar settings em base/development/production
- [ ] 2.2 Separar requirements por ambiente
- [ ] 2.3 Configurar LOGGING
- [ ] 2.4 Adicionar DRF ao INSTALLED_APPS e configurar REST_FRAMEWORK
- [ ] 2.5 Remover `os.makedirs` do settings.py
- [ ] 2.6 Criar `.env.example` com todos os vars necessários

### Fase 3 — Models
- [ ] 3.1 Criar `ISOIndicator` e `ISOIndicatorData` unificados
- [ ] 3.2 Criar data migration dos 4 models antigos → novos
- [ ] 3.3 Criar `Dimension` e `Indicator` models (substituir MOCK_DATA)
- [ ] 3.4 Corrigir User model (email não-nullable, remover `categoria`)
- [ ] 3.5 Corrigir Platform e Norm (snake_case, remover custom PK)
- [ ] 3.6 Adicionar indexes nos campos de filtro mais usados

### Fase 4 — Separação de Apps
- [ ] 4.1 Criar estrutura `apps/` com os 6 apps
- [ ] 4.2 Mover User + auth views → `apps/authentication/`
- [ ] 4.3 Mover user management views → `apps/users/`
- [ ] 4.4 Criar `apps/indicators/` com service layer
- [ ] 4.5 Criar `apps/platforms/`
- [ ] 4.6 Criar `apps/norms/`
- [ ] 4.7 Criar `apps/dashboard/`
- [ ] 4.8 Mover scraping → `apps/scraping/`
- [ ] 4.9 Reorganizar URLs com namespaces
- [ ] 4.10 Atualizar INSTALLED_APPS no settings
- [ ] 4.11 Atualizar todos os imports

### Fase 5 — DRF
- [ ] 5.1 Serializers para indicators
- [ ] 5.2 Serializers para platforms e norms
- [ ] 5.3 Serializers para users
- [ ] 5.4 ViewSets para cada domínio
- [ ] 5.5 Permissions customizadas
- [ ] 5.6 Filtros com django-filter
- [ ] 5.7 Action de upload de anexo no ViewSet
- [ ] 5.8 Router DRF nas URLs

### Fase 6 — Testes
- [ ] 6.1 Configurar pytest-django
- [ ] 6.2 Criar factories com factory-boy
- [ ] 6.3 Testes de segurança (setattr whitelist, year validation, permissions)
- [ ] 6.4 Testes unitários dos services
- [ ] 6.5 Testes de integração das APIs
- [ ] 6.6 Testes de autenticação e autorização
- [ ] 6.7 Cobertura mínima de 80%

### Fase 7 — Performance
- [ ] 7.1 Configurar Redis cache
- [ ] 7.2 Implementar Celery para scraping assíncrono
- [ ] 7.3 Verificar paginação em todos os endpoints
- [ ] 7.4 Adicionar `select_related`/`prefetch_related` nas queries
- [ ] 7.5 Remover view `serve_static` + configurar WhiteNoise

### Fase 8 — Qualidade
- [ ] 8.1 Type hints no código novo
- [ ] 8.2 Context processor para dados do usuário
- [ ] 8.3 Extrair constantes para `constants.py`
- [ ] 8.4 Remover código morto (função `index`, imports duplicados)
- [ ] 8.5 Configurar ruff + mypy

### Fase 9 — Bootstrap
- [ ] 9.1 Baixar Bootstrap 5.3 e Bootstrap Icons para `static/css/` e `static/js/`
- [ ] 9.2 Criar `templates/base.html` com Bootstrap local (remover CDN)
- [ ] 9.3 Criar `templates/base_dashboard.html` com sidebar
- [ ] 9.4 Criar `templates/base_auth.html` para login/register
- [ ] 9.5 Migrar `login.html` para herdar `base_auth.html`
- [ ] 9.6 Migrar `register.html` para herdar `base_auth.html`
- [ ] 9.7 Migrar todos os templates de dashboard para herdar `base_dashboard.html`
- [ ] 9.8 Migrar templates de normas ISO para herdar `base_dashboard.html`
- [ ] 9.9 Migrar templates de admin de usuários para herdar `base_dashboard.html`
- [ ] 9.10 Extrair CSS inline de cada template para `static/css/main.css`
- [ ] 9.11 Criar `templates/components/messages.html` reutilizável
- [ ] 9.12 Criar `templates/components/pagination.html` reutilizável
- [ ] 9.13 Verificar que nenhum template ainda carrega Bootstrap por CDN
- [ ] 9.14 Testar responsividade em mobile (Bootstrap breakpoints)

### Fase 10 — Docker
- [ ] 10.1 Criar `Dockerfile` multi-stage (builder + runner)
- [ ] 10.2 Criar `docker-compose.yml` para desenvolvimento (web + db + redis + celery)
- [ ] 10.3 Criar `docker-compose.prod.yml` com overrides de produção + Nginx
- [ ] 10.4 Criar `nginx/nginx.conf` com HTTPS, cache de static e proxy para Gunicorn
- [ ] 10.5 Criar `.dockerignore`
- [ ] 10.6 Criar `.env.example` com todos os vars necessários (sem valores reais)
- [ ] 10.7 Adicionar `.env` ao `.gitignore`
- [ ] 10.8 Revisar `gunicorn_config.py` (logging para stdout, timeouts)
- [ ] 10.9 Criar endpoint `/health/` no Django para o health check do Docker
- [ ] 10.10 Testar `docker-compose up` do zero (sem estado local)
- [ ] 10.11 Testar `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build`
- [ ] 10.12 Documentar comandos de uso no README

---

## Ordem de Implementação Recomendada

```
Dia 1-2:    Fase 1 completa (segurança — não negociável)
Dia 3:      Fase 2 (settings) + Fase 10 (Docker) em paralelo
Dia 4-6:    Fase 3 (models — o mais impactante)
Dia 7-11:   Fase 4 (separação de apps) + Fase 9 (Bootstrap) em paralelo
Dia 12-15:  Fase 5 (DRF)
Paralelo:   Fase 6 (testes — começar na Fase 3, continuar sempre)
Dia 16-18:  Fase 7 (performance)
Contínuo:   Fase 8 (qualidade)
```

**Docker pode começar no Dia 3** porque não depende de nenhuma refatoração de código — só precisa que o settings esteja separado por ambiente (Fase 2).

**Bootstrap pode começar no Dia 7** em paralelo com a separação de apps, porque a reorganização de templates precisa da nova estrutura de pastas.

---

## Riscos e Dependências

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Data migration dos 4 models ISO falhar | Média | Alto | Testar em banco de dev com dados reais antes |
| Templates quebrarem após renomear campos (`Nome` → `nome`) | Alta | Médio | Buscar todas as referências nos templates antes de renomear |
| URLs existentes quebrarem após reorganização | Alta | Alto | Manter aliases temporários durante transição |
| `MOCK_DATA` sendo usado em template não mapeado | Média | Médio | Grep completo por `MOCK_DATA` antes de remover |
| Credencial DB já comprometida se repo foi público | Alta | Crítico | Rotacionar senha imediatamente na Fase 1 |
| Templates com CSS inline perdendo estilo após migração para Bootstrap | Alta | Médio | Migrar um template por vez e validar no browser antes do próximo |
| Docker volume de banco corrompido ao mudar schema | Baixa | Alto | Usar `docker-compose down -v` apenas em dev, nunca em prod |
| Nginx não encontrar static files em prod | Média | Médio | Verificar que `collectstatic` roda antes do Nginx subir |

---

## O que NÃO fazer

- **Não refatorar e testar ao mesmo tempo**: Testes primeiro, refatoração depois
- **Não renomear campos de modelo sem verificar templates**: Vai quebrar silenciosamente
- **Não remover MOCK_DATA antes de criar os models reais**: O sistema vai quebrar em runtime
- **Não pular a Fase 1**: As vulnerabilidades existem em produção agora
- **Não fazer big-bang**: Uma fase por vez, com deploy e validação entre elas
- **Não commitar `.env`**: Colocar no `.gitignore` antes de qualquer outra coisa
- **Não usar `docker-compose down -v` em produção**: Apaga todos os dados do banco
- **Não misturar CDN e Bootstrap local**: Escolher um e padronizar em todos os templates

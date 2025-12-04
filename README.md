# DataCity

Sistema web Django para coleta e análise de dados com funcionalidades de scraping e gerenciamento de usuários.

## Funcionalidades

- Sistema de autenticação personalizado com login por email
- Módulo de scraping de dados web
- Interface administrativa Django
- Integração com PostgreSQL
- Suporte a análise de dados com pandas e numpy

## Requisitos do Sistema

- Python 3.8+
- PostgreSQL 12+
- Sistema operacional Linux/Ubuntu

## Instalação e Configuração

### 1. Instalar PostgreSQL

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Configurar Banco de Dados

```bash
# Configurar usuário e banco de dados
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres psql -c "ALTER USER postgres CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE datacity OWNER postgres;"
```

### 3. Configurar Ambiente Python

```bash
# Navegar para o diretório do projeto
cd datacity

# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate
```

### 4. Instalar Dependências

```bash
# Instalar dependências essenciais
pip install Django psycopg2-binary requests beautifulsoup4 selenium pandas numpy

# Ou instalar todas as dependências do requirements.txt
pip install -r requirements.txt
```

### 5. Executar Migrações

```bash
# Criar migrações (se necessário)
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate
```

### 6. Criar Superusuário (Opcional)

```bash
# Criar usuário administrador
echo "from accounts.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python manage.py shell
```

### 7. Iniciar o Servidor

```bash
# Ativar ambiente virtual (se não estiver ativo)
source venv/bin/activate

# Iniciar servidor de desenvolvimento
python manage.py runserver
```

## Acesso à Aplicação

- **URL Principal:** http://localhost:8000/
- **Painel Administrativo:** http://localhost:8000/admin/
  - Usuário: `admin`
  - Senha: `admin123`

## Estrutura do Projeto

```
datacity/
├── accounts/           # App de autenticação e usuários
├── scraping/          # App de coleta de dados
├── static/            # Arquivos estáticos (CSS, JS, imagens)
├── templates/         # Templates HTML
├── datacity/          # Configurações principais do projeto
├── manage.py          # Script de gerenciamento Django
├── requirements.txt   # Dependências Python
└── README.md         # Este arquivo
```

## Tecnologias Utilizadas

- **Backend:** Django 5.0.3
- **Banco de Dados:** PostgreSQL
- **Scraping:** BeautifulSoup4, Selenium
- **Análise de Dados:** Pandas, NumPy
- **Frontend:** HTML, CSS, JavaScript

## Desenvolvimento

Para desenvolvimento local, certifique-se de:

1. Ativar sempre o ambiente virtual antes de trabalhar
2. Executar migrações após mudanças nos models
3. Coletar arquivos estáticos se necessário: `python manage.py collectstatic`

## Solução de Problemas

### Erro de Conexão com PostgreSQL
- Verifique se o PostgreSQL está rodando: `sudo systemctl status postgresql`
- Confirme as credenciais no arquivo `settings.py`

### Dependências em Conflito
- Recrie o ambiente virtual e reinstale as dependências

### Portas em Uso
- O servidor roda na porta 8000 por padrão
- Para usar outra porta: `python manage.py runserver 0.0.0.0:8080`
# JavaScript Unificado - Datacity

## Visão Geral

Este diretório contém o arquivo JavaScript unificado (`unified.js`) que combina todas as funcionalidades dos diferentes arquivos JavaScript do projeto Datacity.

## Arquivo Unificado

### `unified.js`
Arquivo principal que contém todas as funcionalidades JavaScript do projeto, incluindo:

- **Funcionalidades de Normas**: Busca, adição, edição e remoção de normas
- **Funcionalidades de Plataformas**: Busca, adição, edição e remoção de plataformas
- **Funcionalidades de Dimensões**: Navegação e gerenciamento de dimensões
- **Funcionalidades de Indicadores**: Exibição e gerenciamento de indicadores
- **Gerenciamento de Modais**: Abertura, fechamento e configuração de modais
- **Utilitários**: Funções auxiliares como CSRF token, cookies, etc.

## Estrutura do Código

O arquivo está organizado em seções bem definidas:

1. **Variáveis Globais**: Dados mockados e variáveis de estado
2. **Inicialização**: Detecção automática do tipo de página
3. **Funcionalidades de Normas**: Tudo relacionado ao gerenciamento de normas
4. **Funcionalidades de Plataformas**: Tudo relacionado ao gerenciamento de plataformas
5. **Funcionalidades de Dimensões e Indicadores**: Navegação e gerenciamento
6. **Funções Utilitárias**: Funções auxiliares reutilizáveis

## Detecção Automática de Página

O arquivo detecta automaticamente o tipo de página e inicializa apenas as funcionalidades necessárias:

- **Páginas de Normas**: Inicializa busca e gerenciamento de normas
- **Páginas de Plataformas**: Inicializa busca e gerenciamento de plataformas
- **Páginas de Dimensões**: Inicializa navegação e gerenciamento de dimensões
- **Páginas de Indicadores**: Inicializa exibição e gerenciamento de indicadores

## Arquivos Substituídos

Os seguintes arquivos foram substituídos pelo `unified.js`:

- `static/script.js`
- `static/js/script.js`
- `static/js/script2.js`
- `static/js/script_templates.js`
- `telas-novas/script.js`

## Como Usar

### Em Templates Django
```html
<script src="{% static 'js/unified.js' %}" defer></script>
```

### Em Arquivos HTML Estáticos
```html
<script src="../static/js/unified.js" defer></script>
```

## Benefícios da Unificação

1. **Manutenibilidade**: Um único arquivo para manter
2. **Performance**: Menos requisições HTTP
3. **Consistência**: Funcionalidades padronizadas
4. **Detecção Automática**: Não precisa especificar qual funcionalidade carregar
5. **Redução de Conflitos**: Elimina conflitos entre diferentes versões

## Compatibilidade

O arquivo unificado é compatível com:
- Todas as páginas existentes do projeto
- Funcionalidades de busca (normas e plataformas)
- Gerenciamento de modais
- Navegação entre dimensões e indicadores
- Operações CRUD para normas e plataformas

## Migração

Todos os arquivos HTML foram atualizados para usar o arquivo unificado. Os arquivos JavaScript antigos foram mantidos por compatibilidade, mas agora apenas redirecionam para o arquivo unificado.

## Desenvolvimento

Para adicionar novas funcionalidades:

1. Adicione o código no arquivo `unified.js`
2. Organize em seções apropriadas
3. Use a função `detectarTipoPagina()` para inicialização automática
4. Teste em todas as páginas relevantes

## Estrutura de Funções

### Funções de Normas
- `inicializarPaginaNormas()`
- `adicionarCaixaBuscaNormas()`
- `ordenarEExibirNormas()`
- `atualizarExibicaoNormas()`
- `filtrarNormas()`
- `adicionarNorma()`
- `editarNorma()`
- `removerNorma()`

### Funções de Plataformas
- `inicializarPaginaPlataformas()`
- `adicionarCaixaBuscaPlataformas()`
- `carregarPlataformas()`
- `adicionarPlataforma()`
- `editarPlataforma()`
- `removerPlataforma()`
- `ordenarEExibirPlataformas()`
- `atualizarExibicaoPlataformas()`
- `filtrarPlataformas()`

### Funções de Dimensões e Indicadores
- `setupDimensoesPage()`
- `setupIndicadoresPage()`
- `carregarIndicadores()`
- `abrirModal()`
- `fecharModal()`
- `carregarModalDjango()`

### Funções Utilitárias
- `getCookie()`
- `abrirPopup()`
- `fecharPopup()`
- `garantirUrlCompleta()`
- `detectarTipoPagina()` 
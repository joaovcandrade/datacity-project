// ========================================
// ARQUIVO JAVASCRIPT UNIFICADO - DATACITY
// ========================================

// ========================================
// VARIÁVEIS GLOBAIS
// ========================================

// Armazenar as normas
let normas = [
   
];

// Armazenar as plataformas
let plataformas = [];

// Dados mockados para simulação
const mockData = {
    dimensoes: [
        { id: 'mobilidade', nome: 'Mobilidade', cor: '#FF8C00', ods: '9, 11', iso: 'ISO 37120' },
        { id: 'urbanismo', nome: 'Urbanismo', cor: '#8A2BE2', ods: '11', iso: 'ISO 37122' },
        { id: 'educacao', nome: 'Educação', cor: 'transparent', ods: '4', iso: 'ISO 37120' },
        { id: 'seguranca', nome: 'Segurança', cor: '#00CED1', ods: '16', iso: 'ISO 37120' },
        { id: 'governanca', nome: 'Governança', cor: '#FF00FF', ods: '16, 17', iso: 'ISO 37122' },
        { id: 'economia', nome: 'Economia', cor: '#32CD32', ods: '8, 9', iso: 'ISO 37120' },
        { id: 'energia', nome: 'Energia', cor: '#FF0000', ods: '7', iso: 'ISO 37120' },
        { id: 'meio-ambiente', nome: 'Meio Ambiente', cor: '#FFD700', ods: '13, 14, 15', iso: 'ISO 37120' },
        { id: 'tecnologia', nome: 'Tecnologia e Inovação', cor: '#1E90FF', ods: '9', iso: 'ISO 37122' },
        { id: 'empreendedorismo', nome: 'Empreendedorismo', cor: '#FF6347', ods: '8', iso: 'ISO 37122' },
        { id: 'saude', nome: 'Saúde', cor: '#FF6B81', ods: '3', iso: 'ISO 37120' }
    ],
    indicadores: {
        'economia': [
            { id: 1, nome: 'PIB per capita', ods: '8', dado: 'R$ 45.000,00', fonte: 'IBGE', iso: 'ISO 37120' },
            { id: 2, nome: 'Taxa de desemprego', ods: '8', dado: '7,5%', fonte: 'IBGE', iso: 'ISO 37120' },
            { id: 3, nome: 'Crescimento anual', ods: '8', dado: '2,3%', fonte: 'Secretaria de Economia', iso: 'ISO 37122' }
        ],
        'educacao': [
            { id: 1, nome: 'Taxa de alfabetização', ods: '4', dado: '97,2%', fonte: 'IBGE', iso: 'ISO 37120' },
            { id: 2, nome: 'Escolas com acesso à internet', ods: '4, 9', dado: '89%', fonte: 'Secretaria de Educação', iso: 'ISO 37122' }
        ],
        'mobilidade': [
            { id: 1, nome: 'Extensão de ciclovias', ods: '11', dado: '85 km', fonte: 'Secretaria de Mobilidade', iso: 'ISO 37120' }
        ]
    }
};

// Constantes para caminhos
const MODAIS_DIMENSOES_PATH = '/modals/dimensoes/';
const MODAIS_INDICADORES_PATH = '/modals/indicadores/';

// ========================================
// INICIALIZAÇÃO
// ========================================

// Função executada quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    // Detectar tipo de página e inicializar funcionalidades apropriadas
    detectarTipoPagina();
});

// Função para detectar o tipo de página e inicializar funcionalidades
function detectarTipoPagina() {
    // Verificar se é página de normas
    if (document.getElementById('menuButtons') && document.querySelector('.nav-buttons')) {
        if (window.location.pathname.includes('normas') || document.title.includes('Normas')) {
            inicializarPaginaNormas();
        } else if (window.location.pathname.includes('plataformas') || document.title.includes('Plataformas')) {
            inicializarPaginaPlataformas();
        }
    }
    
    // Verificar se é página de dimensões
    if (isPaginaDimensoes()) {
        setupDimensoesPage();
    }
    
    // Verificar se é página de indicadores
    if (isPaginaIndicadores()) {
        setupIndicadoresPage();
    }
}

// ========================================
// FUNÇÕES DE DETECÇÃO DE PÁGINA
// ========================================

// Função para verificar se estamos na página de dimensões
function isPaginaDimensoes() {
    return document.getElementById('dimensoes-view') && 
           document.getElementById('dimensoes-view').classList.contains('active');
}

// Função para verificar se estamos na página de indicadores
function isPaginaIndicadores() {
    return document.getElementById('indicadores-view') && 
           document.getElementById('indicadores-view').classList.contains('active');
}

// ========================================
// FUNCIONALIDADES DE NORMAS
// ========================================

// Inicializar página de normas
function inicializarPaginaNormas() {
    adicionarCaixaBuscaNormas();
    carregarNormas();
}

// Função para carregar normas do servidor
async function carregarNormas() {
    try {
        const response = await fetch('/dashboard/normas/listar_normas/');
        const data = await response.json();
        if (data.status === 'success') {
            normas = data.normas;
            ordenarEExibirNormas();
            atualizarSelectsPopupsNormas();
        } else {
            console.error('Erro ao carregar normas:', data.message);
        }
    } catch (error) {
        console.error('Erro ao carregar normas:', error);
    }
}

// Função para adicionar caixa de busca para normas
function adicionarCaixaBuscaNormas() {
    const navButtons = document.querySelector('.nav-buttons');
    if (!navButtons) return;
   
    // Criar o elemento de busca
    const searchContainer = document.createElement('div');
    searchContainer.className = 'search-container';
    searchContainer.style.marginLeft = '15px';
    searchContainer.style.display = 'flex';
    searchContainer.style.alignItems = 'center';
   
    // Criar o input de busca
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.id = 'searchNorma';
    searchInput.placeholder = 'Buscar norma...';
    searchInput.style.padding = '0.5rem';
    searchInput.style.borderRadius = '6px';
    searchInput.style.border = '1px solid #333';
    searchInput.style.backgroundColor = '#2d2d3a';
    searchInput.style.color = '#fff';
   
    // Adicionar evento para filtrar ao digitar
    searchInput.addEventListener('input', filtrarNormas);
   
    // Adicionar o input ao container
    searchContainer.appendChild(searchInput);
   
    // Adicionar o container à navegação
    navButtons.appendChild(searchContainer);
}

// Função para ordenar e exibir normas
function ordenarEExibirNormas() {
    // Ordenar normas alfabeticamente
    normas.sort((a, b) => a.Nome.localeCompare(b.Nome));
   
    // Atualizar a exibição das normas
    atualizarExibicaoNormas();
   
    // Atualizar os selects nos popups
    atualizarSelectsPopupsNormas();
}

// Função para atualizar a exibição das normas
function atualizarExibicaoNormas(filtro = '') {
    const menuButtons = document.getElementById('menuButtons');
    if (!menuButtons) return;
    
    menuButtons.innerHTML = '';
   
    // Filtrar normas se houver um filtro
    const normasFiltradas = filtro
        ? normas.filter(n => n.Nome.toLowerCase().includes(filtro.toLowerCase()))
        : normas;
   
    // Adicionar cada norma ao menu
    normasFiltradas.forEach(norma => {
        const link = document.createElement('a');
        link.href = norma.Direcionamento;
        link.className = 'menu-btn';
        if (norma.Direcionamento.startsWith('http')) {
            link.target = '_blank';
        }
        link.textContent = norma.Nome;
        menuButtons.appendChild(link);
    });
   
    // Mostrar mensagem se não houver resultados
    if (normasFiltradas.length === 0) {
        const mensagem = document.createElement('p');
        mensagem.textContent = 'Nenhuma norma encontrada.';
        mensagem.style.color = '#999';
        mensagem.style.margin = '1rem 0';
        menuButtons.appendChild(mensagem);
    }
}

// Função para filtrar normas
function filtrarNormas() {
    const filtro = document.getElementById('searchNorma').value;
    atualizarExibicaoNormas(filtro);
}

// Função para atualizar os selects nos popups de normas
function atualizarSelectsPopupsNormas() {
    const selectNorma = document.getElementById('selectNorma');
    const removeNorma = document.getElementById('removeNorma');
   
    if (selectNorma) {
        // Limpar opções existentes
        selectNorma.innerHTML = '<option value="">Selecione uma norma</option>';
       
        // Adicionar opções para cada norma
        normas.forEach(norma => {
            const optionEdit = document.createElement('option');
            optionEdit.value = norma.id_norma;
            optionEdit.textContent = norma.Nome;
            selectNorma.appendChild(optionEdit);
        });
    }
    
    if (removeNorma) {
        // Limpar opções existentes
        removeNorma.innerHTML = '<option value="">Selecione uma norma</option>';
       
        // Adicionar opções para cada norma
        normas.forEach(norma => {
            const optionRemove = document.createElement('option');
            optionRemove.value = norma.id_norma;
            optionRemove.textContent = norma.Nome;
            removeNorma.appendChild(optionRemove);
        });
    }
}

// Função para adicionar uma nova norma
async function adicionarNorma() {
    const nome = document.getElementById('nomeNorma').value.trim();
    const link = garantirUrlCompleta(document.getElementById('linkNorma').value.trim());
   
    // Validar campos
    if (!nome || !link) {
        alert('Preencha todos os campos.');
        return;
    }
   
    try {
        const response = await fetch('/dashboard/normas/adicionar_norma/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `name=${encodeURIComponent(nome)}&link=${encodeURIComponent(link)}`
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Recarregar normas
            await carregarNormas();
            // Fechar popup
            fecharPopup('adicionar-norma');
            // Mensagem de sucesso
            alert('Norma adicionada com sucesso!');
        } else {
            alert('Erro ao adicionar norma: ' + data.message);
        }
    } catch (error) {
        console.error('Erro ao adicionar norma:', error);
        alert('Erro ao adicionar norma. Tente novamente.');
    }
}

// Função para editar norma
async function editarNorma() {
    const normaId = document.getElementById('selectNorma').value;
    const novoNome = document.getElementById('editNomeNorma').value.trim();
    const novoLink = garantirUrlCompleta(document.getElementById('editLinkNorma').value.trim());
   
    // Validar campos
    if (!normaId || !novoNome || !novoLink) {
        alert('Preencha todos os campos.');
        return;
    }
   
    try {
        const response = await fetch(`/dashboard/normas/editar_norma/${normaId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `name=${encodeURIComponent(novoNome)}&link=${encodeURIComponent(novoLink)}`
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Recarregar normas
            await carregarNormas();
            // Fechar popup
            fecharPopup('editar-norma');
            // Mensagem de sucesso
            alert('Norma editada com sucesso!');
        } else {
            alert('Erro ao editar norma: ' + data.message);
        }
    } catch (error) {
        console.error('Erro ao editar norma:', error);
        alert('Erro ao editar norma. Tente novamente.');
    }
}

// Função para remover norma
async function removerNorma() {
    const normaId = document.getElementById('removeNorma').value;
   
    // Validar seleção
    if (!normaId) {
        alert('Selecione uma norma para remover.');
        return;
    }
   
    // Confirmar remoção
    if (confirm('Tem certeza que deseja remover esta norma?')) {
        try {
            const response = await fetch(`/dashboard/normas/remover_norma/${normaId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Recarregar normas
                await carregarNormas();
                // Fechar popup
                fecharPopup('remover-norma');
                // Mensagem de sucesso
                alert('Norma removida com sucesso!');
            } else {
                alert('Erro ao remover norma: ' + data.message);
            }
        } catch (error) {
            console.error('Erro ao remover norma:', error);
            alert('Erro ao remover norma. Tente novamente.');
        }
    }
}

// ========================================
// FUNCIONALIDADES DE PLATAFORMAS
// ========================================

// Inicializar página de plataformas
function inicializarPaginaPlataformas() {
    adicionarCaixaBuscaPlataformas();
    carregarPlataformas();
}

// Função para adicionar caixa de busca para plataformas
function adicionarCaixaBuscaPlataformas() {
    const navButtons = document.querySelector('.nav-buttons');
    if (!navButtons) return;
   
    // Criar o elemento de busca
    const searchContainer = document.createElement('div');
    searchContainer.className = 'search-container';
    searchContainer.style.marginLeft = '15px';
    searchContainer.style.display = 'flex';
    searchContainer.style.alignItems = 'center';
   
    // Criar o input de busca
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.id = 'searchPlataforma';
    searchInput.placeholder = 'Buscar plataforma...';
    searchInput.style.padding = '0.5rem';
    searchInput.style.borderRadius = '6px';
    searchInput.style.border = '1px solid #333';
    searchInput.style.backgroundColor = '#2d2d3a';
    searchInput.style.color = '#fff';
   
    // Adicionar evento para filtrar ao digitar
    searchInput.addEventListener('input', filtrarPlataformas);
   
    // Adicionar o input ao container
    searchContainer.appendChild(searchInput);
   
    // Adicionar o container à navegação
    navButtons.appendChild(searchContainer);
}

// Função para carregar plataformas do servidor
async function carregarPlataformas() {
    try {
        const response = await fetch('/dashboard/plataformas/listar/');
        const data = await response.json();
        
        if (data.status === 'success') {
            plataformas = data.plataformas;
            ordenarEExibirPlataformas();
            atualizarSelectsPopupsPlataformas();
        } else {
            console.error('Erro ao carregar plataformas:', data.message);
        }
    } catch (error) {
        console.error('Erro ao carregar plataformas:', error);
    }
}

// Função para garantir que a URL tenha o protocolo
function garantirUrlCompleta(link) {
    if (!link.startsWith('http://') && !link.startsWith('https://')) {
        return 'https://' + link;
    }
    return link;
}

// Função para adicionar uma nova plataforma
async function adicionarPlataforma() {
    const nome = document.getElementById('nomePlataforma').value.trim();
    const link = garantirUrlCompleta(document.getElementById('linkPlataforma').value.trim());
   
    // Validar campos
    if (!nome || !link) {
        alert('Preencha todos os campos.');
        return;
    }
   
    try {
        const response = await fetch('/dashboard/plataformas/adicionar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `name=${encodeURIComponent(nome)}&link=${encodeURIComponent(link)}`
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Recarregar plataformas
            await carregarPlataformas();
            // Fechar popup
            fecharPopup('adicionar');
            // Mensagem de sucesso
            alert('Plataforma adicionada com sucesso!');
        } else {
            alert('Erro ao adicionar plataforma: ' + data.message);
        }
    } catch (error) {
        console.error('Erro ao adicionar plataforma:', error);
        alert('Erro ao adicionar plataforma. Tente novamente.');
    }
}

// Função para editar plataforma
async function editarPlataforma() {
    const plataformaId = document.getElementById('selectPlataforma').value;
    const novoNome = document.getElementById('editNomePlataforma').value.trim();
    const novoLink = garantirUrlCompleta(document.getElementById('editLinkPlataforma').value.trim());
   
    // Validar campos
    if (!plataformaId || !novoNome || !novoLink) {
        alert('Preencha todos os campos.');
        return;
    }
   
    try {
        const response = await fetch(`/dashboard/plataformas/editar/${plataformaId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `name=${encodeURIComponent(novoNome)}&link=${encodeURIComponent(novoLink)}`
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Recarregar plataformas
            await carregarPlataformas();
            // Fechar popup
            fecharPopup('editar');
            // Mensagem de sucesso
            alert('Plataforma editada com sucesso!');
        } else {
            alert('Erro ao editar plataforma: ' + data.message);
        }
    } catch (error) {
        console.error('Erro ao editar plataforma:', error);
        alert('Erro ao editar plataforma. Tente novamente.');
    }
}

// Função para remover plataforma
async function removerPlataforma() {
    const plataformaId = document.getElementById('removePlataforma').value;
   
    // Validar seleção
    if (!plataformaId) {
        alert('Selecione uma plataforma para remover.');
        return;
    }
   
    // Confirmar remoção
    if (confirm('Tem certeza que deseja remover esta plataforma?')) {
        try {
            const response = await fetch(`/dashboard/plataformas/remover/${plataformaId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Recarregar plataformas
                await carregarPlataformas();
                // Fechar popup
                fecharPopup('remover');
                // Mensagem de sucesso
                alert('Plataforma removida com sucesso!');
            } else {
                alert('Erro ao remover plataforma: ' + data.message);
            }
        } catch (error) {
            console.error('Erro ao remover plataforma:', error);
            alert('Erro ao remover plataforma. Tente novamente.');
        }
    }
}

// Função para ordenar e exibir plataformas
function ordenarEExibirPlataformas() {
    // Ordenar plataformas alfabeticamente
    plataformas.sort((a, b) => a.name.localeCompare(b.name));
   
    // Atualizar a exibição
    atualizarExibicaoPlataformas();
}

// Função para atualizar a exibição das plataformas
function atualizarExibicaoPlataformas(filtro = '') {
    const menuButtons = document.getElementById('menuButtons');
    if (!menuButtons) return;
    
    menuButtons.innerHTML = '';
   
    // Filtrar plataformas se houver um filtro
    const plataformasFiltradas = filtro
        ? plataformas.filter(p => p.name.toLowerCase().includes(filtro.toLowerCase()))
        : plataformas;
   
    // Adicionar cada plataforma ao menu
    plataformasFiltradas.forEach(plataforma => {
        const link = document.createElement('a');
        link.href = plataforma.link;
        link.className = 'menu-btn';
        link.target = '_blank';
        link.textContent = plataforma.name;
        menuButtons.appendChild(link);
    });
   
    // Mostrar mensagem se não houver resultados
    if (plataformasFiltradas.length === 0) {
        const mensagem = document.createElement('p');
        mensagem.textContent = 'Nenhuma plataforma encontrada.';
        mensagem.style.color = '#999';
        mensagem.style.margin = '1rem 0';
        menuButtons.appendChild(mensagem);
    }
}

// Função para filtrar plataformas
function filtrarPlataformas() {
    const filtro = document.getElementById('searchPlataforma').value;
    atualizarExibicaoPlataformas(filtro);
}

// Função para atualizar os selects nos popups de plataformas
function atualizarSelectsPopupsPlataformas() {
    const selectPlataforma = document.getElementById('selectPlataforma');
    const removePlataforma = document.getElementById('removePlataforma');
   
    if (selectPlataforma) {
        // Limpar opções existentes
        selectPlataforma.innerHTML = '<option value="">Selecione uma plataforma</option>';
       
        // Adicionar opções para cada plataforma
        plataformas.forEach(plataforma => {
            const optionEdit = document.createElement('option');
            optionEdit.value = plataforma.id;
            optionEdit.textContent = plataforma.name;
            selectPlataforma.appendChild(optionEdit);
        });
    }
    
    if (removePlataforma) {
        // Limpar opções existentes
        removePlataforma.innerHTML = '<option value="">Selecione uma plataforma</option>';
       
        // Adicionar opções para cada plataforma
        plataformas.forEach(plataforma => {
            const optionRemove = document.createElement('option');
            optionRemove.value = plataforma.id;
            optionRemove.textContent = plataforma.name;
            removePlataforma.appendChild(optionRemove);
        });
    }
}

// ========================================
// FUNCIONALIDADES DE DIMENSÕES E INDICADORES
// ========================================

// Gerenciamento de modais
function abrirModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
    }
}

function fecharModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
    }
}

function fecharTodosModais() {
    const modais = document.querySelectorAll('.modal');
    modais.forEach(modal => modal.classList.remove('show'));
}

// Para fechar modais clicando fora deles
window.addEventListener('click', function(e) {
    const modais = document.querySelectorAll('.modal');
    modais.forEach(modal => {
        if (e.target === modal) {
            modal.classList.remove('show');
        }
    });
});

// Manipulação da tela de dimensões
function setupDimensoesPage() {
    if (!isPaginaDimensoes()) return;

    // Clique em dimensões para navegar para indicadores
    const dimensoes = document.querySelectorAll('.dimension-item');
    dimensoes.forEach(dim => {
        dim.addEventListener('click', function() {
            const dimensaoId = this.getAttribute('data-dimension');
            const dimensaoNome = this.querySelector('.dimension-name').textContent;
            
            // Em um cenário real, você redirecionaria para a página de indicadores
            // Por enquanto, simulamos a navegação alterando o src do iframe no index
            if (window.parent && window.parent !== window) {
                const iframe = window.parent.document.getElementById('content-frame');
                if (iframe) {
                    // Salvar a dimensão selecionada no sessionStorage para recuperá-la na página de indicadores
                    sessionStorage.setItem('dimensaoSelecionada', dimensaoId);
                    sessionStorage.setItem('dimensaoNome', dimensaoNome);
                    
                    iframe.src = '/indicadores';
                } else {
                    // Fallback para redirecionamento direto se não estiver em um iframe
                    window.location.href = '/indicadores';
                }
            } else {
                // Fallback para redirecionamento direto se não estiver em um iframe
                sessionStorage.setItem('dimensaoSelecionada', dimensaoId);
                sessionStorage.setItem('dimensaoNome', dimensaoNome);
                window.location.href = '/indicadores';
            }
        });
    });

    // Eventos para os botões de gerenciamento de dimensões
    const novaDimensaoBtn = document.getElementById('nova-dimensao-btn');
    if (novaDimensaoBtn) {
        novaDimensaoBtn.addEventListener('click', function() {
            // Carregar modal a partir do Django template
            carregarModalDjango(MODAIS_DIMENSOES_PATH, 'nova-dimensao-modal');
        });
    }

    const editarDimensaoBtn = document.getElementById('editar-dimensao-btn');
    if (editarDimensaoBtn) {
        editarDimensaoBtn.addEventListener('click', function() {
            // Carregar modal a partir do Django template
            carregarModalDjango(MODAIS_DIMENSOES_PATH, 'editar-dimensao-modal');
        });
    }

    const removerDimensaoBtn = document.getElementById('remover-dimensao-btn');
    if (removerDimensaoBtn) {
        removerDimensaoBtn.addEventListener('click', function() {
            // Carregar modal a partir do Django template
            carregarModalDjango(MODAIS_DIMENSOES_PATH, 'remover-dimensao-modal');
        });
    }

    // Configurar eventos para formulários de dimensões
    document.addEventListener('submit', function(e) {
        if (e.target.id === 'nova-dimensao-form') {
            e.preventDefault();
            // Lógica para salvar nova dimensão
            fecharModal('nova-dimensao-modal');
        } else if (e.target.id === 'editar-dimensao-form') {
            e.preventDefault();
            // Lógica para editar dimensão
            fecharModal('editar-dimensao-modal');
        } else if (e.target.id === 'remover-dimensao-form') {
            e.preventDefault();
            // Lógica para remover dimensão
            fecharModal('remover-dimensao-modal');
        }
    });

    // Botão de cancelar remover
    document.addEventListener('click', function(e) {
        if (e.target.id === 'cancelar-remover') {
            fecharModal('remover-dimensao-modal');
        }
    });
}

// Função para carregar modal a partir do Django template
function carregarModalDjango(templatePath, modalId) {
    // Cria um elemento temporário para conter o modal
    const tempContainer = document.createElement('div');
    tempContainer.id = 'temp-modal-container';
    document.body.appendChild(tempContainer);
    
    // Faz uma requisição para o Django para obter o template renderizado
    fetch(templatePath)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro ao carregar o modal: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            // Insere o HTML no contêiner temporário
            tempContainer.innerHTML = html;
            
            // Localiza o modal específico no HTML
            const modalElement = document.getElementById(modalId);
            
            if (modalElement) {
                // Abre o modal
                abrirModal(modalId);
                
                // Configura eventos para o modal recém-carregado
                configureModalEvents(modalId);
            } else {
                console.error(`Modal não encontrado: ${modalId}`);
            }
        })
        .catch(error => {
            console.error('Erro ao carregar modal:', error);
        });
}

// Função para configurar eventos dos modais
function configureModalEvents(modalId) {
    // Configurar eventos específicos para cada tipo de modal
    if (modalId === 'nova-dimensao-modal') {
        const form = document.getElementById('nova-dimensao-form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                // Lógica para salvar nova dimensão
                fecharModal(modalId);
            });
        }
    } else if (modalId === 'editar-dimensao-modal') {
        const form = document.getElementById('editar-dimensao-form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                // Lógica para editar dimensão
                fecharModal(modalId);
            });
        }
    } else if (modalId === 'remover-dimensao-modal') {
        const form = document.getElementById('remover-dimensao-form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                // Lógica para remover dimensão
                fecharModal(modalId);
            });
        }
        
        const cancelarBtn = document.getElementById('cancelar-remover');
        if (cancelarBtn) {
            cancelarBtn.addEventListener('click', function() {
                fecharModal(modalId);
            });
        }
    }
}

// Manipulação da tela de indicadores
function setupIndicadoresPage() {
    if (!isPaginaIndicadores()) return;

    // Recuperar informações da dimensão selecionada
    const dimensaoId = sessionStorage.getItem('dimensaoSelecionada') || 'economia';
    const dimensaoNome = sessionStorage.getItem('dimensaoNome') || 'Economia';
    
    // Atualizar título com o nome da dimensão
    const dimensaoNomeElement = document.getElementById('dimensao-nome');
    if (dimensaoNomeElement) {
        dimensaoNomeElement.textContent = dimensaoNome;
    }
    
    // Carregar os indicadores da dimensão selecionada
    carregarIndicadores(dimensaoId);
    
    // Configurar botão de voltar
    const voltarBtn = document.getElementById('voltar-dimensoes-btn');
    if (voltarBtn) {
        voltarBtn.addEventListener('click', function() {
            if (window.parent && window.parent !== window) {
                const iframe = window.parent.document.getElementById('content-frame');
                if (iframe) {
                    iframe.src = '/dimensoes';
                } else {
                    window.location.href = '/dimensoes';
                }
            } else {
                window.location.href = '/dimensoes';
            }
        });
    }

    // Eventos para os botões de gerenciamento de indicadores
    const novoIndicadorBtn = document.getElementById('novo-indicador-btn');
    if (novoIndicadorBtn) {
        novoIndicadorBtn.addEventListener('click', function() {
            carregarModalDjango(MODAIS_INDICADORES_PATH, 'novo-indicador-modal');
        });
    }

    const editarIndicadorBtn = document.getElementById('editar-indicador-btn');
    if (editarIndicadorBtn) {
        editarIndicadorBtn.addEventListener('click', function() {
            carregarModalDjango(MODAIS_INDICADORES_PATH, 'editar-indicador-modal');
        });
    }

    const removerIndicadorBtn = document.getElementById('remover-indicador-btn');
    if (removerIndicadorBtn) {
        removerIndicadorBtn.addEventListener('click', function() {
            carregarModalDjango(MODAIS_INDICADORES_PATH, 'remover-indicador-modal');
        });
    }
}

// Função para carregar indicadores
function carregarIndicadores(dimensaoId) {
    const indicadoresContainer = document.getElementById('indicadores-container');
    if (!indicadoresContainer) return;

    const indicadores = mockData.indicadores[dimensaoId] || [];
    
    indicadoresContainer.innerHTML = '';
    
    if (indicadores.length === 0) {
        const mensagem = document.createElement('p');
        mensagem.textContent = 'Nenhum indicador disponível para esta dimensão.';
        mensagem.style.color = '#999';
        mensagem.style.textAlign = 'center';
        mensagem.style.margin = '2rem 0';
        indicadoresContainer.appendChild(mensagem);
        return;
    }
    
    indicadores.forEach(indicador => {
        const indicadorElement = document.createElement('div');
        indicadorElement.className = 'indicador-item';
        indicadorElement.innerHTML = `
            <h3>${indicador.nome}</h3>
            <p><strong>Dado:</strong> ${indicador.dado}</p>
            <p><strong>Fonte:</strong> ${indicador.fonte}</p>
            <p><strong>ODS:</strong> ${indicador.ods}</p>
            <p><strong>ISO:</strong> ${indicador.iso}</p>
        `;
        indicadoresContainer.appendChild(indicadorElement);
    });
}

// ========================================
// FUNÇÕES UTILITÁRIAS
// ========================================

// Função para obter o token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Função para abrir popup (genérica)
function abrirPopup(tipo) {
    const popup = document.getElementById(`popup-${tipo}`);
    if (popup) {
        popup.style.display = 'flex';
        
        // Configurar eventos específicos baseado no tipo
        if (tipo === 'editar') {
            const selectPlataforma = document.getElementById('selectPlataforma');
            if (selectPlataforma) {
                selectPlataforma.addEventListener('change', function() {
                    const plataformaSelecionada = plataformas.find(p => p.id === parseInt(this.value));
                    if (plataformaSelecionada) {
                        document.getElementById('editNomePlataforma').value = plataformaSelecionada.name;
                        document.getElementById('editLinkPlataforma').value = plataformaSelecionada.link;
                    } else {
                        document.getElementById('editNomePlataforma').value = '';
                        document.getElementById('editLinkPlataforma').value = '';
                    }
                });
            }
        } else if (tipo === 'editar-norma') {
            const selectNorma = document.getElementById('selectNorma');
            if (selectNorma) {
                selectNorma.addEventListener('change', function() {
                    const normaSelecionada = normas.find(n => n.id === parseInt(this.value));
                    if (normaSelecionada) {
                        document.getElementById('editNomeNorma').value = normaSelecionada.name;
                        document.getElementById('editLinkNorma').value = normaSelecionada.link;
                    } else {
                        document.getElementById('editNomeNorma').value = '';
                        document.getElementById('editLinkNorma').value = '';
                    }
                });
            }
        }
    }
}

// Função para fechar popup (genérica)
function fecharPopup(tipo) {
    const popup = document.getElementById(`popup-${tipo}`);
    if (popup) {
        popup.style.display = 'none';
        
        // Limpar campos baseado no tipo
        if (tipo === 'adicionar') {
            const nomeInput = document.getElementById('nomePlataforma');
            const linkInput = document.getElementById('linkPlataforma');
            if (nomeInput) nomeInput.value = '';
            if (linkInput) linkInput.value = '';
        } else if (tipo === 'editar') {
            const selectPlataforma = document.getElementById('selectPlataforma');
            const editNomeInput = document.getElementById('editNomePlataforma');
            const editLinkInput = document.getElementById('editLinkPlataforma');
            if (selectPlataforma) selectPlataforma.value = '';
            if (editNomeInput) editNomeInput.value = '';
            if (editLinkInput) editLinkInput.value = '';
        } else if (tipo === 'remover') {
            const removePlataforma = document.getElementById('removePlataforma');
            if (removePlataforma) removePlataforma.value = '';
        } else if (tipo === 'adicionar-norma') {
            const nomeInput = document.getElementById('nomeNorma');
            const linkInput = document.getElementById('linkNorma');
            if (nomeInput) nomeInput.value = '';
            if (linkInput) linkInput.value = '';
        } else if (tipo === 'editar-norma') {
            const selectNorma = document.getElementById('selectNorma');
            const editNomeInput = document.getElementById('editNomeNorma');
            const editLinkInput = document.getElementById('editLinkNorma');
            if (selectNorma) selectNorma.value = '';
            if (editNomeInput) editNomeInput.value = '';
            if (editLinkInput) editLinkInput.value = '';
        } else if (tipo === 'remover-norma') {
            const removeNorma = document.getElementById('removeNorma');
            if (removeNorma) removeNorma.value = '';
        }
    }
}

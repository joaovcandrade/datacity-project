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
        // Outros indicadores podem ser adicionados conforme necessário
    }
};

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
            window.parent.document.body.appendChild(document.getElementById('nova-dimensao-modal').cloneNode(true));
            abrirModal('nova-dimensao-modal');
        });
    }

    const editarDimensaoBtn = document.getElementById('editar-dimensao-btn');
    if (editarDimensaoBtn) {
        editarDimensaoBtn.addEventListener('click', function() {
            window.parent.document.body.appendChild(document.getElementById('editar-dimensao-modal').cloneNode(true));
            abrirModal('editar-dimensao-modal');
        });
    }

    const removerDimensaoBtn = document.getElementById('remover-dimensao-btn');
    if (removerDimensaoBtn) {
        removerDimensaoBtn.addEventListener('click', function() {
            window.parent.document.body.appendChild(document.getElementById('remover-dimensao-modal').cloneNode(true));
            abrirModal('remover-dimensao-modal');
        });
    }

    // Formulários de dimensões
    const novaDimensaoForm = document.getElementById('nova-dimensao-form');
    if (novaDimensaoForm) {
        novaDimensaoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // Lógica para salvar nova dimensão
            fecharModal('nova-dimensao-modal');
        });
    }

    const editarDimensaoForm = document.getElementById('editar-dimensao-form');
    if (editarDimensaoForm) {
        editarDimensaoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // Lógica para editar dimensão
            fecharModal('editar-dimensao-modal');
        });
    }

    const removerDimensaoForm = document.getElementById('remover-dimensao-form');
    if (removerDimensaoForm) {
        removerDimensaoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // Lógica para remover dimensão
            fecharModal('remover-dimensao-modal');
        });
    }

    // Botão de cancelar remover
    const cancelarRemoverBtn = document.getElementById('cancelar-remover');
    if (cancelarRemoverBtn) {
        cancelarRemoverBtn.addEventListener('click', function() {
            fecharModal('remover-dimensao-modal');
        });
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
                    iframe.src = 'dimensoes.html';
                } else {
                    window.location.href = 'dimensoes.html';
                }
            } else {
                window.location.href = 'dimensoes.html';
            }
        });
    }
    
    // Botões de ação
    const adicionarIndicadorBtn = document.getElementById('adicionar-indicador-btn');
    if (adicionarIndicadorBtn) {
        adicionarIndicadorBtn.addEventListener('click', function() {
            // Carregar os modais dos indicadores
            const modaisIndicadores = document.createElement('div');
            fetch('modals-indicadores.html')
                .then(response => response.text())
                .then(html => {
                    modaisIndicadores.innerHTML = html;
                    document.body.appendChild(modaisIndicadores);
                    abrirModal('adicionar-indicador-modal');
                });
        });
    }
    
    const editarIndicadorBtn = document.getElementById('editar-indicador-btn');
    if (editarIndicadorBtn) {
        editarIndicadorBtn.addEventListener('click', function() {
            // Carregar os modais dos indicadores
            const modaisIndicadores = document.createElement('div');
            fetch('modals-indicadores.html')
                .then(response => response.text())
                .then(html => {
                    modaisIndicadores.innerHTML = html;
                    document.body.appendChild(modaisIndicadores);
                    
                    // Preencher select com os indicadores
                    const selectIndicador = document.getElementById('editar-select-indicador');
                    const indicadores = mockData.indicadores[dimensaoId] || [];
                    indicadores.forEach(ind => {
                        const option = document.createElement('option');
                        option.value = ind.id;
                        option.textContent = ind.nome;
                        selectIndicador.appendChild(option);
                    });
                    
                    abrirModal('editar-indicador-modal');
                });
        });
    }
    
    const excluirIndicadorBtn = document.getElementById('excluir-indicador-btn');
    if (excluirIndicadorBtn) {
        excluirIndicadorBtn.addEventListener('click', function() {
            // Carregar os modais dos indicadores
            const modaisIndicadores = document.createElement('div');
            fetch('modals-indicadores.html')
                .then(response => response.text())
                .then(html => {
                    modaisIndicadores.innerHTML = html;
                    document.body.appendChild(modaisIndicadores);
                    
                    // Preencher select com os indicadores
                    const selectIndicador = document.getElementById('excluir-select-indicador');
                    const indicadores = mockData.indicadores[dimensaoId] || [];
                    indicadores.forEach(ind => {
                        const option = document.createElement('option');
                        option.value = ind.id;
                        option.textContent = ind.nome;
                        selectIndicador.appendChild(option);
                    });
                    
                    abrirModal('excluir-indicador-modal');
                });
        });
    }
    
    // Garantir que temos event listeners para os formulários de indicadores
    document.addEventListener('submit', function(e) {
        if (e.target.id === 'adicionar-indicador-form') {
            e.preventDefault();
            // Lógica para adicionar indicador
            fecharModal('adicionar-indicador-modal');
        } else if (e.target.id === 'editar-indicador-form') {
            e.preventDefault();
            // Lógica para editar indicador
            fecharModal('editar-indicador-modal');
        } else if (e.target.id === 'excluir-indicador-form') {
            e.preventDefault();
            // Lógica para excluir indicador
            fecharModal('excluir-indicador-modal');
        }
    });
    
    // Botão de cancelar excluir indicador
    document.addEventListener('click', function(e) {
        if (e.target.id === 'cancelar-excluir-indicador') {
            fecharModal('excluir-indicador-modal');
        }
    });
}

// Carregar indicadores na tabela
function carregarIndicadores(dimensaoId) {
    const tabela = document.getElementById('indicadores-table');
    if (!tabela) return;
    
    const tbody = tabela.querySelector('tbody');
    tbody.innerHTML = ''; // Limpar conteúdo atual
    
    const indicadores = mockData.indicadores[dimensaoId] || [];
    
    if (indicadores.length === 0) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 5;
        td.textContent = 'Nenhum indicador cadastrado para esta dimensão.';
        td.style.textAlign = 'center';
        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
    }
    
    indicadores.forEach(ind => {
        const tr = document.createElement('tr');
        
        // Nome do indicador
        const tdNome = document.createElement('td');
        tdNome.textContent = ind.nome;
        tr.appendChild(tdNome);
        
        // ODS
        const tdODS = document.createElement('td');
        tdODS.textContent = ind.ods || '-';
        tr.appendChild(tdODS);
        
        // Dado
        const tdDado = document.createElement('td');
        tdDado.textContent = ind.dado || '-';
        tr.appendChild(tdDado);
        
        // Fonte
        const tdFonte = document.createElement('td');
        tdFonte.textContent = ind.fonte || '-';
        tr.appendChild(tdFonte);
        
        // ISO
        const tdISO = document.createElement('td');
        tdISO.textContent = ind.iso || '-';
        tr.appendChild(tdISO);
        
        tbody.appendChild(tr);
    });
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Verifica em qual página estamos e configura os eventos adequados
    setupDimensoesPage();
    setupIndicadoresPage();
    
    // Se estamos no index.html com o iframe, configuramos os eventos para comunicação entre frames
    const contentFrame = document.getElementById('content-frame');
    if (contentFrame) {
        contentFrame.onload = function() {
            // Quando o iframe carrega, podemos tentar acessar seu conteúdo
            try {
                const frameWindow = contentFrame.contentWindow;
                // Fazer algo com frameWindow, se necessário
            } catch (e) {
                console.error("Erro ao acessar o iframe:", e);
            }
        };
    }
});

// Carregamento de modais a partir de arquivos externos
function carregarModais() {
    if (isPaginaDimensoes()) {
        // Carrega os modais das dimensões
        fetch('modals-dimensoes.html')
            .then(response => response.text())
            .then(html => {
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = html;
                
                // Extrai os modais e adiciona ao documento atual
                const modais = tempDiv.querySelectorAll('.modal');
                modais.forEach(modal => {
                    document.body.appendChild(modal);
                });
                
                // Reconfigura os eventos para os novos elementos
                setupDimensoesPage();
            })
            .catch(error => console.error('Erro ao carregar modais:', error));
    }
}

// Chama a função para carregar modais quando a página estiver pronta
document.addEventListener('DOMContentLoaded', carregarModais);
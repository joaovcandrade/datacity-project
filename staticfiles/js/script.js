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

// Constantes para caminhos
const MODAIS_DIMENSOES_PATH = '/modals/dimensoes/';  // URL Django em vez do caminho do arquivo
const MODAIS_INDICADORES_PATH = '/modals/indicadores/'; 

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

// Configurar eventos para modais carregados dinamicamente
function configureModalEvents(modalId) {
    // Configurar formulários
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
            // Preencher select com as dimensões
            const selectDimensao = document.getElementById('editar-select-dimensao');
            if (selectDimensao) {
                mockData.dimensoes.forEach(dim => {
                    const option = document.createElement('option');
                    option.value = dim.id;
                    option.textContent = dim.nome;
                    selectDimensao.appendChild(option);
                });
            }
            
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                // Lógica para editar dimensão
                fecharModal(modalId);
            });
        }
    } else if (modalId === 'remover-dimensao-modal') {
        const form = document.getElementById('remover-dimensao-form');
        if (form) {
            // Preencher select com as dimensões
            const selectDimensao = document.getElementById('remover-select-dimensao');
            if (selectDimensao) {
                mockData.dimensoes.forEach(dim => {
                    const option = document.createElement('option');
                    option.value = dim.id;
                    option.textContent = dim.nome;
                    selectDimensao.appendChild(option);
                });
            }
            
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                // Lógica para remover dimensão
                fecharModal(modalId);
            });
            
            // Botão de cancelar
            const cancelarBtn = document.getElementById('cancelar-remover');
            if (cancelarBtn) {
                cancelarBtn.addEventListener('click', function() {
                    fecharModal(modalId);
                });
            }
        }
    } else if (modalId === 'adicionar-indicador-modal') {
        const form = document.getElementById('adicionar-indicador-form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                // Lógica para adicionar indicador
                fecharModal(modalId);
            });
        }
    } else if (modalId === 'editar-indicador-modal') {
        const form = document.getElementById('editar-indicador-form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                // Lógica para editar indicador
                fecharModal(modalId);
            });
        }
    } else if (modalId === 'excluir-indicador-modal') {
        const form = document.getElementById('excluir-indicador-form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                // Lógica para excluir indicador
                fecharModal(modalId);
            });
            
            // Botão de cancelar
            const cancelarBtn = document.getElementById('cancelar-excluir-indicador');
            if (cancelarBtn) {
                cancelarBtn.addEventListener('click', function() {
                    fecharModal(modalId);
                });
            }
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
                    iframe.src = 'dimensoes.html';
                } else {
                    window.location.href = 'dimensoes.html';
                }
            } else {
                window.location.href = 'dimensoes.html';
            }
        });
    }
    
    // Botões de ação de indicadores
    const adicionarIndicadorBtn = document.getElementById('adicionar-indicador-btn');
    if (adicionarIndicadorBtn) {
        adicionarIndicadorBtn.addEventListener('click', function() {
            // Carregar modal a partir do Django template
            carregarModalDjango(MODAIS_INDICADORES_PATH, 'adicionar-indicador-modal');
        });
    }
    
    const editarIndicadorBtn = document.getElementById('editar-indicador-btn');
    if (editarIndicadorBtn) {
        editarIndicadorBtn.addEventListener('click', function() {
            // Carregar modal a partir do Django template
            carregarModalDjango(MODAIS_INDICADORES_PATH, 'editar-indicador-modal', function() {
                // Callback após carregar o modal
                // Preencher select com os indicadores
                const selectIndicador = document.getElementById('editar-select-indicador');
                if (selectIndicador) {
                    const dimensaoId = sessionStorage.getItem('dimensaoSelecionada') || 'economia';
                    const indicadores = mockData.indicadores[dimensaoId] || [];
                    indicadores.forEach(ind => {
                        const option = document.createElement('option');
                        option.value = ind.id;
                        option.textContent = ind.nome;
                        selectIndicador.appendChild(option);
                    });
                }
            });
        });
    }
    
    const excluirIndicadorBtn = document.getElementById('excluir-indicador-btn');
    if (excluirIndicadorBtn) {
        excluirIndicadorBtn.addEventListener('click', function() {
            // Carregar modal a partir do Django template
            carregarModalDjango(MODAIS_INDICADORES_PATH, 'excluir-indicador-modal', function() {
                // Callback após carregar o modal
                // Preencher select com os indicadores
                const selectIndicador = document.getElementById('excluir-select-indicador');
                if (selectIndicador) {
                    const dimensaoId = sessionStorage.getItem('dimensaoSelecionada') || 'economia';
                    const indicadores = mockData.indicadores[dimensaoId] || [];
                    indicadores.forEach(ind => {
                        const option = document.createElement('option');
                        option.value = ind.id;
                        option.textContent = ind.nome;
                        selectIndicador.appendChild(option);
                    });
                }
            });
        });
    }
}

// Função modificada para carregar modal com callback opcional
function carregarModalDjango(templatePath, modalId, callback) {
    fetch(templatePath)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro ao carregar o modal: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            // Criar um container temporário para o HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            
            // Encontrar o modal específico no HTML
            const modal = tempDiv.querySelector(`#${modalId}`);
            
            if (modal) {
                // Adicionar o modal ao documento
                document.body.appendChild(modal);
                
                // Configurar eventos para o modal
                configureModalEvents(modalId);
                
                // Abrir o modal
                abrirModal(modalId);
                
                // Executar callback se fornecido
                if (callback && typeof callback === 'function') {
                    callback();
                }
            } else {
                console.error(`Modal não encontrado: ${modalId}`);
            }
        })
        .catch(error => {
            console.error('Erro ao carregar modal:', error);
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
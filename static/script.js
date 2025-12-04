// Armazenar as normas
let normas = [
    { nome: 'ISO 37120', link: 'iso37120.html' },
    { nome: 'ISO 37122', link: 'iso37122.html' },
    { nome: 'ISO 37123', link: 'iso37123.html' }
];

// Armazenar as plataformas
let plataformas = [];

// Função executada quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar caixa de busca
    adicionarCaixaBusca();
    // Ordenar e exibir normas
    ordenarEExibirNormas();
    // Carregar plataformas do servidor
    carregarPlataformas();
});

// Função para adicionar caixa de busca
function adicionarCaixaBusca() {
    const navButtons = document.querySelector('.nav-buttons');
   
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
    normas.sort((a, b) => a.nome.localeCompare(b.nome));
   
    // Atualizar a exibição das normas
    atualizarExibicaoNormas();
   
    // Atualizar os selects nos popups
    atualizarSelectsPopups();
}

// Função para atualizar a exibição das normas
function atualizarExibicaoNormas(filtro = '') {
    const menuButtons = document.getElementById('menuButtons');
    menuButtons.innerHTML = '';
   
    // Filtrar normas se houver um filtro
    const normasFiltradas = filtro
        ? normas.filter(n => n.nome.toLowerCase().includes(filtro.toLowerCase()))
        : normas;
   
    // Adicionar cada norma ao menu
    normasFiltradas.forEach(norma => {
        const link = document.createElement('a');
        link.href = norma.link;
        link.className = 'menu-btn';
        if (norma.link.startsWith('http')) {
            link.target = '_blank';
        }
        link.textContent = norma.nome;
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

// Função para atualizar os selects nos popups
function atualizarSelectsPopups() {
    const selectNorma = document.getElementById('selectNorma');
    const removeNorma = document.getElementById('removeNorma');
   
    // Limpar opções existentes
    selectNorma.innerHTML = '<option value="">Selecione uma norma</option>';
    removeNorma.innerHTML = '<option value="">Selecione uma norma</option>';
   
    // Adicionar opções para cada norma
    normas.forEach(norma => {
        // Adicionar ao select de edição
        const optionEdit = document.createElement('option');
        optionEdit.value = norma.nome;
        optionEdit.textContent = norma.nome;
        selectNorma.appendChild(optionEdit);
       
        // Adicionar ao select de remoção
        const optionRemove = document.createElement('option');
        optionRemove.value = norma.nome;
        optionRemove.textContent = norma.nome;
        removeNorma.appendChild(optionRemove);
    });
}

// Função para abrir popup
function abrirPopup(tipo) {
    document.getElementById(`popup-${tipo}`).style.display = 'flex';
   
    // Se for edição, configurar o evento de seleção de norma
    if (tipo === 'editar-norma') {
        const selectNorma = document.getElementById('selectNorma');
        selectNorma.addEventListener('change', function() {
            const normaSelecionada = normas.find(n => n.nome === this.value);
            if (normaSelecionada) {
                document.getElementById('editNomeNorma').value = normaSelecionada.nome;
                document.getElementById('editLinkNorma').value = normaSelecionada.link;
            } else {
                document.getElementById('editNomeNorma').value = '';
                document.getElementById('editLinkNorma').value = '';
            }
        });
    }
}

// Função para fechar popup
function fecharPopup(tipo) {
    document.getElementById(`popup-${tipo}`).style.display = 'none';
   
    // Limpar campos
    if (tipo === 'adicionar-norma') {
        document.getElementById('nomeNorma').value = '';
        document.getElementById('linkNorma').value = '';
    } else if (tipo === 'editar-norma') {
        document.getElementById('selectNorma').value = '';
        document.getElementById('editNomeNorma').value = '';
        document.getElementById('editLinkNorma').value = '';
    } else if (tipo === 'remover-norma') {
        document.getElementById('removeNorma').value = '';
    }
}

// Função para adicionar uma nova norma
function adicionarNorma() {
    const nome = document.getElementById('nomeNorma').value.trim();
    const link = document.getElementById('linkNorma').value.trim() || `${nome.toLowerCase().replace(/\s+/g, '')}.html`;
   
    // Validar campos
    if (!nome) {
        alert('Preencha pelo menos o nome da norma.');
        return;
    }
   
    // Verificar se já existe uma norma com esse nome
    if (normas.some(n => n.nome.toLowerCase() === nome.toLowerCase())) {
        alert('Já existe uma norma com esse nome.');
        return;
    }
   
    // Adicionar norma
    normas.push({ nome, link });
   
    // Ordenar e exibir normas
    ordenarEExibirNormas();
   
    // Fechar popup
    fecharPopup('adicionar-norma');
   
    // Mensagem de sucesso
    alert('Norma adicionada com sucesso!');
}

// Função para editar norma
function editarNorma() {
    const normaSelecionada = document.getElementById('selectNorma').value;
    const novoNome = document.getElementById('editNomeNorma').value.trim();
    const novoLink = document.getElementById('editLinkNorma').value.trim();
   
    // Validar campos
    if (!normaSelecionada || !novoNome) {
        alert('Preencha pelo menos o nome da norma.');
        return;
    }
   
    // Verificar se o novo nome já existe para outra norma
    if (novoNome !== normaSelecionada &&
        normas.some(n => n.nome.toLowerCase() === novoNome.toLowerCase())) {
        alert('Já existe uma norma com esse nome.');
        return;
    }
   
    // Atualizar norma
    const index = normas.findIndex(n => n.nome === normaSelecionada);
    if (index !== -1) {
        // Se o link estiver vazio, criar um novo a partir do nome
        const link = novoLink || `${novoNome.toLowerCase().replace(/\s+/g, '')}.html`;
        normas[index] = { nome: novoNome, link: link };
       
        // Ordenar e exibir normas
        ordenarEExibirNormas();
       
        // Fechar popup
        fecharPopup('editar-norma');
       
        // Mensagem de sucesso
        alert('Norma editada com sucesso!');
    }
}

// Função para remover norma
function removerNorma() {
    const normaSelecionada = document.getElementById('removeNorma').value;
   
    // Validar seleção
    if (!normaSelecionada) {
        alert('Selecione uma norma para remover.');
        return;
    }
   
    // Confirmar remoção
    if (confirm(`Tem certeza que deseja remover a norma ${normaSelecionada}?`)) {
        // Remover norma
        normas = normas.filter(n => n.nome !== normaSelecionada);
       
        // Atualizar exibição
        ordenarEExibirNormas();
       
        // Fechar popup
        fecharPopup('remover-norma');
       
        // Mensagem de sucesso
        alert('Norma removida com sucesso!');
    }
}

// Função para carregar plataformas do servidor
async function carregarPlataformas() {
    try {
        const response = await fetch('/dashboard/plataformas/listar/');
        const data = await response.json();
        
        if (data.status === 'success') {
            plataformas = data.plataformas;
            ordenarEExibirPlataformas();
            atualizarSelectsPopups();
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

// Função para atualizar os selects nos popups
function atualizarSelectsPopups() {
    const selectPlataforma = document.getElementById('selectPlataforma');
    const removePlataforma = document.getElementById('removePlataforma');
   
    // Limpar opções existentes
    selectPlataforma.innerHTML = '<option value="">Selecione uma plataforma</option>';
    removePlataforma.innerHTML = '<option value="">Selecione uma plataforma</option>';
   
    // Adicionar opções para cada plataforma
    plataformas.forEach(plataforma => {
        // Adicionar ao select de edição
        const optionEdit = document.createElement('option');
        optionEdit.value = plataforma.id;
        optionEdit.textContent = plataforma.name;
        selectPlataforma.appendChild(optionEdit);
       
        // Adicionar ao select de remoção
        const optionRemove = document.createElement('option');
        optionRemove.value = plataforma.id;
        optionRemove.textContent = plataforma.name;
        removePlataforma.appendChild(optionRemove);
    });
}

// Função para abrir popup
function abrirPopup(tipo) {
    document.getElementById(`popup-${tipo}`).style.display = 'flex';
   
    // Se for edição, configurar o evento de seleção de plataforma
    if (tipo === 'editar') {
        const selectPlataforma = document.getElementById('selectPlataforma');
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
}

// Função para fechar popup
function fecharPopup(tipo) {
    document.getElementById(`popup-${tipo}`).style.display = 'none';
   
    // Limpar campos
    if (tipo === 'adicionar') {
        document.getElementById('nomePlataforma').value = '';
        document.getElementById('linkPlataforma').value = '';
    } else if (tipo === 'editar') {
        document.getElementById('selectPlataforma').value = '';
        document.getElementById('editNomePlataforma').value = '';
        document.getElementById('editLinkPlataforma').value = '';
    } else if (tipo === 'remover') {
        document.getElementById('removePlataforma').value = '';
    }
}
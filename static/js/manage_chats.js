// static/js/manage_chats.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Elementos da UI ---
    const chatListDiv = document.getElementById('chatList');
    const chatDescriptionInput = document.getElementById('chatDescription');
    const chatModeSelectCreate = document.getElementById('chatMode'); // Select do form de criação
    const btnCreateChat = document.getElementById('btnCreateChat');
    const btnRefreshList = document.getElementById('btnRefreshList');
    const statusMessageDiv = document.getElementById('statusMessage');

    // <<< ADICIONADO: Verificações de Nulo >>>
    if (!chatListDiv) console.error("DEBUG ERROR: Elemento 'chatList' não encontrado!");
    if (!chatDescriptionInput) console.error("DEBUG ERROR: Elemento 'chatDescription' não encontrado!");
    if (!chatModeSelectCreate) console.error("DEBUG ERROR: Elemento 'chatMode' (select criação) não encontrado!");
    if (!btnCreateChat) console.error("DEBUG ERROR: Elemento 'btnCreateChat' não encontrado!");
    if (!btnRefreshList) console.error("DEBUG ERROR: Elemento 'btnRefreshList' não encontrado!");
    if (!statusMessageDiv) console.error("DEBUG ERROR: Elemento 'statusMessage' não encontrado!");
    // <<< FIM DAS VERIFICAÇÕES >>>


    // --- Configurações ---
    const API_BASE_URL = 'http://localhost:8050';
    const availableModes = ["Default", "Code", "Architect", "Debug", "Ask"];

    // --- Estado do Frontend ---
    let currentActiveChatId = null;
    let currentChatList = [];
    let statusTimeout;

    // --- Funções da API (fetchChatsAndActive, renderChatList, createChat, etc...) ---
    // (Cole aqui as funções completas da resposta anterior - #32)
    // Elas não precisam de alteração para este erro específico.
    // Vou colar elas aqui para garantir que está completo:

    async function fetchChatsAndActive() {
        showMessage('Buscando chats e status ativo...', false);
        chatListDiv.innerHTML = '<p>Carregando lista de chats...</p>';
        currentChatList = [];
        try {
            const activeResponse = await fetch(`${API_BASE_URL}/v1/chats/active`);
            if (!activeResponse.ok) { const eT = await activeResponse.text(); throw new Error(`Chat ativo: ${activeResponse.status} ${eT}`);}
            const activeData = await activeResponse.json();
            currentActiveChatId = activeData.active_chat_id;
            console.log("Active Chat ID:", currentActiveChatId); // Log ID ativo

            const listResponse = await fetch(`${API_BASE_URL}/v1/chats`);
            if (!listResponse.ok) { const eT = await listResponse.text(); throw new Error(`Lista chats: ${listResponse.status} ${eT}`);}
            currentChatList = await listResponse.json();

            renderChatList(currentChatList);
            showMessage('Lista de chats atualizada.', false);
        } catch (error) {
            console.error('Erro fetchChatsAndActive:', error);
            renderChatList([]); showMessage(`Erro ao buscar dados: ${error.message}`, true);
            currentActiveChatId = null;
        }
    }

    function renderChatList(chats) {
        chatListDiv.innerHTML = '';
        if (!chats || chats.length === 0) { chatListDiv.innerHTML = '<p>Nenhum chat encontrado.</p>'; return; }
        const table = document.createElement('table');
        table.innerHTML = `<thead><tr><th class="col-desc">Descrição</th><th class="col-mode">Modo</th><th class="col-id">Chat ID</th><th class="col-actions">Ações</th></tr></thead><tbody></tbody>`;
        const tbody = table.querySelector('tbody');
        chats.forEach(chat => {
            const isActive = (chat.chat_id === currentActiveChatId);
            const tr = document.createElement('tr');
            const tdDesc = document.createElement('td'); tdDesc.innerHTML = chat.description || '<em>Sem descrição</em>'; tr.appendChild(tdDesc);
            const tdMode = document.createElement('td'); const modeSelect = document.createElement('select'); modeSelect.dataset.chatId = chat.chat_id; modeSelect.title = "Mudar modo";
            availableModes.forEach(modeOption => {
                const option = document.createElement('option'); option.value = modeOption; option.textContent = modeOption;
                if ((chat.mode || "Default") === modeOption) { option.selected = true; }
                modeSelect.appendChild(option);
            });
            modeSelect.addEventListener('change', handleModeChange); tdMode.appendChild(modeSelect); tr.appendChild(tdMode);
            const tdId = document.createElement('td'); tdId.innerHTML = `<code>${chat.chat_id}</code>`; tr.appendChild(tdId);
            const tdActions = document.createElement('td'); const activateButton = document.createElement('button'); activateButton.dataset.chatId = chat.chat_id;
            if (isActive) { activateButton.textContent = 'Ativo'; activateButton.className = 'btn-is-active'; activateButton.title = 'Ativo (Clique p/ desativar)'; activateButton.addEventListener('click', () => deactivateChat()); }
            else { activateButton.textContent = 'Definir Ativo'; activateButton.className = 'btn-set-active'; activateButton.title = 'Definir como ativo'; activateButton.addEventListener('click', () => setActiveChat(chat.chat_id)); }
            tdActions.appendChild(activateButton);
            const deleteButton = document.createElement('button'); deleteButton.textContent = 'Deletar'; deleteButton.className = 'btn-delete'; deleteButton.dataset.chatId = chat.chat_id; deleteButton.dataset.chatDesc = chat.description || chat.chat_id; deleteButton.title = 'Deletar chat'; deleteButton.addEventListener('click', (e) => deleteChat(e.target.dataset.chatId, e.target.dataset.chatDesc)); tdActions.appendChild(deleteButton);
            tr.appendChild(tdActions); tbody.appendChild(tr);
        });
        chatListDiv.appendChild(table);
    }

    async function createChat() {
        if (!chatDescriptionInput || !chatModeSelectCreate) { // Checagem extra
             showMessage("Erro: Elementos do formulário não encontrados.", true); return;
        }
        const description = chatDescriptionInput.value.trim();
        const mode = chatModeSelectCreate.value;
        showMessage(`Criando chat (Modo: ${mode})...`, false);
        try {
            const response = await fetch(`${API_BASE_URL}/v1/chats`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ description: description || null, mode: mode }) });
            if (!response.ok) { const e = await response.json().catch(()=>({detail:`Erro ${response.status}`})); throw new Error(`${response.status} - ${e.detail}`); }
            const newChatId = await response.json(); showMessage(`Chat "${description||newChatId}" (Modo: ${mode}) criado. ID: ${newChatId}`, false);
            chatDescriptionInput.value = ''; chatModeSelectCreate.value = "Default"; fetchChatsAndActive();
        } catch (error) { console.error('Erro createChat:', error); showMessage(`Erro ao criar: ${error.message}`, true); }
    }

    function handleModeChange(event) { const selectElement = event.target; const chatId = selectElement.dataset.chatId; const newMode = selectElement.value; updateChatMode(chatId, newMode); }

    async function updateChatMode(chatId, newMode) {
        showMessage(`Atualizando modo do chat ${chatId} para ${newMode}...`, false);
        try {
            const response = await fetch(`${API_BASE_URL}/v1/chats/${chatId}/mode`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: newMode }) });
            if (!response.ok) { const e = await response.json().catch(()=>({detail:`Erro ${response.status}`})); throw new Error(`${response.status} - ${e.detail}`); }
            const result = await response.json(); showMessage(result.message || `Modo de ${chatId} atualizado.`, false);
            fetchChatsAndActive();
        } catch (error) { console.error('Erro updateChatMode:', error); showMessage(`Erro ao atualizar modo: ${error.message}`, true); fetchChatsAndActive(); }
    }

    async function setActiveChat(chatId) {
        showMessage(`Definindo chat ${chatId} como ativo...`, false);
        try {
            const response = await fetch(`${API_BASE_URL}/v1/chats/active`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chat_id: chatId }) });
            if (!response.ok) { const e = await response.json().catch(()=>({detail:`Erro ${response.status}`})); throw new Error(`${response.status} - ${e.detail}`); }
            const result = await response.json(); showMessage(result.message || `Chat ${chatId} ativo.`, false);
            fetchChatsAndActive();
        } catch (error) { console.error('Erro setActiveChat:', error); showMessage(`Erro ao ativar: ${error.message}`, true); }
    }

     async function deactivateChat() {
        showMessage(`Desativando chat ativo...`, false);
        try {
            const response = await fetch(`${API_BASE_URL}/v1/chats/active`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chat_id: null }) });
            if (!response.ok) { const e = await response.json().catch(()=>({detail:`Erro ${response.status}`})); throw new Error(`${response.status} - ${e.detail}`); }
            const result = await response.json(); showMessage(result.message || `Chat ativo desativado.`, false);
            fetchChatsAndActive();
        } catch (error) { console.error('Erro deactivateChat:', error); showMessage(`Erro ao desativar: ${error.message}`, true); }
    }

    async function deleteChat(chatId, chatDesc) {
        if (!confirm(`Deletar chat "${chatDesc}" (ID: ${chatId})?`)) return;
        showMessage(`Deletando chat ${chatId}...`, false);
        try {
            const response = await fetch(`${API_BASE_URL}/v1/chats/${chatId}`, { method: 'DELETE' });
            if (response.status === 204) { showMessage(`Chat ${chatId} deletado.`, false); fetchChatsAndActive(); }
            else { const e = await response.json().catch(()=>({detail:`Erro ${response.status}`})); throw new Error(`${response.status} - ${e.detail}`); }
        } catch (error) { console.error('Erro deleteChat:', error); showMessage(`Erro ao deletar ${chatId}: ${error.message}`, true); }
    }

    function showMessage(message, isError = false) {
        if(!statusMessageDiv) return; // Não tenta mostrar se o elemento não existe
        statusMessageDiv.textContent = message; statusMessageDiv.className = isError ? 'status-error' : 'status-success'; statusMessageDiv.style.display = 'block';
        clearTimeout(statusTimeout); statusTimeout = setTimeout(() => { statusMessageDiv.style.display = 'none'; }, 5000);
    }

    // --- Event Listeners Iniciais ---
    // <<< ADICIONADO: Verificações antes de adicionar listener >>>
    if (btnRefreshList) {
        btnRefreshList.addEventListener('click', fetchChatsAndActive);
    } else {
        console.error("Falha ao adicionar listener: Botão 'btnRefreshList' não encontrado.");
    }

    if (btnCreateChat) {
        btnCreateChat.addEventListener('click', createChat);
    } else {
        console.error("Falha ao adicionar listener: Botão 'btnCreateChat' não encontrado.");
    }


    // --- Carga Inicial ---
    // Popula as opções do select de criação dinamicamente
    if (chatModeSelectCreate) { // Verifica se o select existe
        availableModes.forEach(mode => {
            const option = document.createElement('option');
            option.value = mode;
            option.textContent = mode;
            chatModeSelectCreate.appendChild(option);
        });
        console.log("Select de modo populado."); // Log de sucesso
    } else {
        console.error("Falha ao popular modos: Select 'chatMode' (criação) não encontrado.");
    }

    // Busca os dados iniciais ao carregar a página
    fetchChatsAndActive();
    console.log("Gerenciador de Chats inicializado.");

}); // Fim do DOMContentLoaded
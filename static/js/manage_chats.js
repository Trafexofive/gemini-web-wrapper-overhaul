document.addEventListener('DOMContentLoaded', () => {
    // Elementos da UI
    const chatListDiv = document.getElementById('chatList');
    // const activeChatStatusDiv = document.getElementById('activeChatStatus'); // Removido
    const chatDescriptionInput = document.getElementById('chatDescription');
    const btnCreateChat = document.getElementById('btnCreateChat');
    const btnRefreshList = document.getElementById('btnRefreshList');
    // const btnDeactivate = document.getElementById('btnDeactivate'); // Removido
    const statusMessageDiv = document.getElementById('statusMessage');

    // URL base da API
    const API_BASE_URL = 'http://localhost:8050';

    // <<< Variável para guardar o ID do chat ativo no frontend >>>
    let currentActiveChatId = null;
    // <<< Variável para guardar a lista de chats atual (cache leve) >>>
    let currentChatList = [];

    // --- Funções da API ---

    // Busca a lista de chats E o chat ativo
    async function fetchChatsAndActive() {
        showMessage('Buscando chats e status ativo...', false);
        chatListDiv.innerHTML = '<p>Carregando lista de chats...</p>';
        currentChatList = []; // Limpa cache

        try {
            // Busca o chat ativo PRIMEIRO
            const activeResponse = await fetch(`${API_BASE_URL}/v1/chats/active`);
            if (!activeResponse.ok) {
                throw new Error(`Erro ao buscar chat ativo: ${activeResponse.status}`);
            }
            const activeData = await activeResponse.json();
            currentActiveChatId = activeData.active_chat_id; // Atualiza variável global
            console.log("Active Chat ID fetched:", currentActiveChatId);

            // Busca a lista de chats
            const listResponse = await fetch(`${API_BASE_URL}/v1/chats`);
            if (!listResponse.ok) {
                throw new Error(`Erro ao buscar lista de chats: ${listResponse.status} ${listResponse.statusText}`);
            }
            currentChatList = await listResponse.json(); // Atualiza cache

            // Renderiza a lista com o estado ativo atualizado
            renderChatList(currentChatList);
            showMessage('Lista de chats atualizada.', false);

        } catch (error) {
            console.error('Erro em fetchChatsAndActive:', error);
            renderChatList([]); // Limpa a lista em caso de erro
            showMessage(`Erro ao buscar dados: ${error.message}`, true);
            currentActiveChatId = null; // Reseta em caso de erro
        }
    }

    // Renderiza a lista de chats na tabela, ajustando os botões
    function renderChatList(chats) {
        chatListDiv.innerHTML = ''; // Limpa conteúdo anterior

        if (!chats || chats.length === 0) {
            chatListDiv.innerHTML = '<p>Nenhum chat encontrado.</p>';
            return;
        }

        const table = document.createElement('table');
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Descrição</th>
                    <th>Chat ID</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
            </tbody>
        `;
        const tbody = table.querySelector('tbody');

        chats.forEach(chat => {
            const isActive = (chat.chat_id === currentActiveChatId); // Verifica se é o ativo
            const tr = document.createElement('tr');

            // Botão Ativar/Desativar
            let actionButtonHtml;
            if (isActive) {
                actionButtonHtml = `<button class="btn-is-active" data-chat-id="${chat.chat_id}" title="Clique para desativar este chat">Ativo</button>`;
            } else {
                actionButtonHtml = `<button class="btn-set-active" data-chat-id="${chat.chat_id}" title="Clique para definir este chat como ativo">Definir Ativo</button>`;
            }

            tr.innerHTML = `
                <td>${chat.description || '<em>Sem descrição</em>'}</td>
                <td><code>${chat.chat_id}</code></td>
                <td>
                    ${actionButtonHtml}
                    <button class="btn-delete" data-chat-id="${chat.chat_id}" data-chat-desc="${chat.description || chat.chat_id}" title="Deletar este chat permanentemente">Deletar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        chatListDiv.appendChild(table);

        // Adiciona listeners aos botões da lista
        // Botão "Ativo" agora chama deactivateChat
        table.querySelectorAll('.btn-is-active').forEach(button => {
            button.addEventListener('click', () => deactivateChat()); // Não precisa de ID, desativa o atual
        });
        // Botão "Definir Ativo" chama setActiveChat
        table.querySelectorAll('.btn-set-active').forEach(button => {
            button.addEventListener('click', () => setActiveChat(button.dataset.chatId));
        });
        table.querySelectorAll('.btn-delete').forEach(button => {
            button.addEventListener('click', () => deleteChat(button.dataset.chatId, button.dataset.chatDesc));
        });
    }

    // Cria um novo chat
    async function createChat() {
        const description = chatDescriptionInput.value.trim();
        showMessage('Criando chat...', false);
        try {
            const response = await fetch(`${API_BASE_URL}/v1/chats`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ description: description || null })
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido' }));
                throw new Error(`Erro ao criar chat: ${response.status} - ${errorData.detail || response.statusText}`);
            }
            const newChatId = await response.json();
            showMessage(`Chat "${description || newChatId}" criado com sucesso (ID: ${newChatId}).`, false);
            chatDescriptionInput.value = '';
            fetchChatsAndActive(); // Atualiza tudo
        } catch (error) {
            console.error('Erro em createChat:', error);
            showMessage(`Erro ao criar chat: ${error.message}`, true);
        }
    }

    // Define o chat ativo
    async function setActiveChat(chatId) {
        showMessage(`Definindo chat ${chatId} como ativo...`, false);
        try {
            const response = await fetch(`${API_BASE_URL}/v1/chats/active`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_id: chatId })
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido' }));
                throw new Error(`Erro ao definir chat ativo: ${response.status} - ${errorData.detail || response.statusText}`);
            }
            const result = await response.json();
            showMessage(result.message || `Chat ${chatId} definido como ativo.`, false);
            // Atualiza o ID ativo localmente e recarrega a lista para refletir a mudança visual
            // currentActiveChatId = chatId; // fetchChatsAndActive vai buscar o valor atualizado da API
            fetchChatsAndActive();
        } catch (error) {
            console.error('Erro em setActiveChat:', error);
            showMessage(`Erro ao definir chat ativo: ${error.message}`, true);
        }
    }

     // Desativa o chat ativo (define como null)
     async function deactivateChat() {
        showMessage(`Desativando chat ativo...`, false);
        try {
            const response = await fetch(`${API_BASE_URL}/v1/chats/active`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_id: null }) // Envia null
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido' }));
                throw new Error(`Erro ao desativar chat: ${response.status} - ${errorData.detail || response.statusText}`);
            }
            const result = await response.json();
            showMessage(result.message || `Chat ativo desativado.`, false);
            // Atualiza o ID ativo localmente e recarrega a lista
            // currentActiveChatId = null; // fetchChatsAndActive vai buscar o valor atualizado da API
            fetchChatsAndActive();
        } catch (error) {
            console.error('Erro em deactivateChat:', error);
            showMessage(`Erro ao desativar chat ativo: ${error.message}`, true);
        }
    }

    // Deleta um chat
    async function deleteChat(chatId, chatDesc) {
        if (!confirm(`Tem certeza que deseja deletar o chat "${chatDesc}" (ID: ${chatId})?`)) {
            return;
        }
        showMessage(`Deletando chat ${chatId}...`, false);
        try {
            const response = await fetch(`${API_BASE_URL}/v1/chats/${chatId}`, { method: 'DELETE' });
            if (response.status === 204) {
                showMessage(`Chat ${chatId} deletado com sucesso.`, false);
                // Se o chat deletado era o ativo, a API já limpou no backend.
                // Apenas recarregamos tudo para mostrar o estado correto.
                fetchChatsAndActive();
            } else {
                const errorData = await response.json().catch(() => ({ detail: `Erro ${response.status}` }));
                throw new Error(`Erro ao deletar chat: ${response.status} - ${errorData.detail || response.statusText}`);
            }
        } catch (error) {
            console.error('Erro em deleteChat:', error);
            showMessage(`Erro ao deletar chat ${chatId}: ${error.message}`, true);
        }
    }

    // Mostra mensagens de status
    let statusTimeout;
    function showMessage(message, isError = false) {
        statusMessageDiv.textContent = message;
        statusMessageDiv.className = isError ? 'status-error' : 'status-success';
        statusMessageDiv.style.display = 'block';
        clearTimeout(statusTimeout);
        statusTimeout = setTimeout(() => {
            statusMessageDiv.style.display = 'none';
        }, 5000);
    }

    // --- Event Listeners Iniciais ---
    btnRefreshList.addEventListener('click', fetchChatsAndActive);
    btnCreateChat.addEventListener('click', createChat);
    // Listener para o botão de desativar global foi removido

    // --- Carga Inicial ---
    fetchChatsAndActive(); // Busca a lista E o status ativo ao carregar

});
// static/js/manage_chats.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Configuration ---
    const API_BASE_URL = 'http://localhost:8022';
    const AVAILABLE_MODES = ["Default", "Code", "Architect", "Debug", "Ask"]; // Use const

    // --- State ---
    const state = {
        currentActiveChatId: null,
        currentChatList: [],
        statusTimeout: null,
    };

    // --- DOM Elements ---
    const elements = {
        chatListDiv: document.getElementById('chatList'),
        chatDescriptionInput: document.getElementById('chatDescription'),
        chatModeSelectCreate: document.getElementById('chatMode'),
        btnCreateChat: document.getElementById('btnCreateChat'),
        btnRefreshList: document.getElementById('btnRefreshList'),
        statusMessageDiv: document.getElementById('statusMessage'),
    };

    // Basic validation that essential elements exist
    for (const key in elements) {
        if (!elements[key]) {
            console.error(`ERROR: UI Element '${key}' not found! Check HTML ID.`);
            // Optional: Halt execution if critical elements missing
            if (key === 'chatListDiv' || key === 'statusMessageDiv') {
                 document.body.innerHTML = `<h1>Error: Critical UI element missing (${key}). Cannot initialize application.</h1>`;
                 return;
            }
        }
    }

    // --- API Service ---
    /**
     * Generic fetch wrapper for API calls. Handles common error checking.
     * @param {string} endpoint - API endpoint (e.g., '/v1/chats')
     * @param {object} options - Fetch options (method, headers, body)
     * @returns {Promise<any>} - Promise resolving with JSON data or null for 204
     * @throws {Error} - Throws an error for network issues or non-ok responses
     */
    async function _fetchApi(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        try {
            const response = await fetch(url, options);

            if (!response.ok) {
                let errorDetail = `HTTP error ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.detail || JSON.stringify(errorData) || errorDetail;
                } catch (e) {
                    errorDetail = response.statusText || errorDetail;
                }
                throw new Error(`API Error (${response.status}): ${errorDetail}`);
            }

            if (response.status === 204) {
                return null; // Handle No Content
            }
            return await response.json(); // Assume JSON for other success cases

        } catch (error) {
            console.error(`Workspace failed for ${url}:`, error);
            throw error; // Re-throw for the caller to handle UI feedback
        }
    }

    // Namespaced API functions using the helper
    const api = {
        getActiveChatId: () => _fetchApi('/v1/chats/active'),
        getChats: () => _fetchApi('/v1/chats'),
        createChat: (description, mode) => _fetchApi('/v1/chats', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: description || null, mode: mode }),
        }),
        updateChatMode: (chatId, newMode) => _fetchApi(`/v1/chats/${chatId}/mode`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: newMode }),
        }),
        setActiveChat: (chatId) => _fetchApi('/v1/chats/active', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: chatId }),
        }),
        deactivateChat: () => _fetchApi('/v1/chats/active', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: null }),
        }),
        deleteChat: (chatId) => _fetchApi(`/v1/chats/${chatId}`, { method: 'DELETE' }),
    };


    // --- UI Manager ---
    const ui = {
        /** Shows a status message to the user. */
        showMessage: (message, isError = false) => {
            if (!elements.statusMessageDiv) return;
            elements.statusMessageDiv.textContent = message;
            elements.statusMessageDiv.className = isError ? 'status-error' : 'status-success';
            elements.statusMessageDiv.style.display = 'block';

            clearTimeout(state.statusTimeout);
            state.statusTimeout = setTimeout(() => {
                if (elements.statusMessageDiv) elements.statusMessageDiv.style.display = 'none';
            }, 5000);
        },

        /** Renders the list of chats in the table. */
        renderChatList: () => {
            const chats = state.currentChatList;
            const activeId = state.currentActiveChatId;

            if (!elements.chatListDiv) return; // Guard against missing element

            // Ensure the table structure exists, create if not
             let tbody = elements.chatListDiv.querySelector('tbody');
             if (!tbody) {
                elements.chatListDiv.innerHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th class="col-desc">Description</th>
                                <th class="col-mode">Mode</th>
                                <th class="col-id">Chat ID</th>
                                <th class="col-actions">Actions</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                     </table>`;
                tbody = elements.chatListDiv.querySelector('tbody'); // Get the new tbody
             }

            // Clear only the tbody content
            tbody.innerHTML = '';

            if (!chats || chats.length === 0) {
                // If table exists but no chats, show message inside div, replacing table
                elements.chatListDiv.innerHTML = '<p>Nenhum chat encontrado.</p>';
                return;
            }

            // Use DocumentFragment for efficient bulk appending
            const fragment = document.createDocumentFragment();
            chats.forEach(chat => {
                const isActive = (chat.chat_id === activeId);
                const tr = document.createElement('tr');
                // Store chat data directly on the row for delegation handlers
                tr.dataset.chatId = chat.chat_id;
                tr.dataset.chatDesc = chat.description || chat.chat_id;

                tr.innerHTML = `
                    <td>${chat.description || '<em>Sem descrição</em>'}</td>
                    <td>
                        <select class="mode-select" title="Mudar modo">
                            ${AVAILABLE_MODES.map(modeOption => `
                                <option value="${modeOption}" ${ (chat.mode || "Default") === modeOption ? 'selected' : '' }>
                                    ${modeOption}
                                </option>
                            `).join('')}
                        </select>
                    </td>
                    <td><code>${chat.chat_id}</code></td>
                    <td>
                        <button
                            class="btn-activate ${isActive ? 'btn-is-active' : 'btn-set-active'}"
                            data-action="${isActive ? 'deactivate' : 'activate'}"
                            title="${isActive ? 'Active (Click to deactivate)' : 'Make active'}"
                        >
                            ${isActive ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                            class="btn-delete"
                            data-action="delete"
                            title="Delete chat"
                        >
                            Delete
                        </button>
                    </td>
                `;
                fragment.appendChild(tr);
            });
            tbody.appendChild(fragment);
        },

        /** Populates the 'Create Chat' mode select dropdown. */
        populateCreateModeSelect: () => {
            if (!elements.chatModeSelectCreate) return;
            elements.chatModeSelectCreate.innerHTML = ''; // Clear existing options
            AVAILABLE_MODES.forEach(mode => {
                const option = document.createElement('option');
                option.value = mode;
                option.textContent = mode;
                elements.chatModeSelectCreate.appendChild(option);
            });
             elements.chatModeSelectCreate.value = "Default"; // Set default
        },

         /** Clears the create chat form inputs. */
        clearCreateForm: () => {
            if (elements.chatDescriptionInput) elements.chatDescriptionInput.value = '';
            if (elements.chatModeSelectCreate) elements.chatModeSelectCreate.value = "Default";
        }
    };

    // --- Event Handlers ---

    /** Main function to refresh chat list and active status from API. */
    async function refreshChatData() {
        ui.showMessage('Buscando chats e status ativo...', false);
        if(elements.chatListDiv) elements.chatListDiv.innerHTML = '<p>Loading chats list...</p>';

        try {
            const [chatsData, activeData] = await Promise.all([
                api.getChats(),
                api.getActiveChatId()
            ]);

            state.currentChatList = chatsData || [];
            state.currentActiveChatId = activeData?.active_chat_id ?? null;

            ui.renderChatList(); // Render based on updated state
            // Only show success if not initially empty, prevent message flashing on load
             if (state.currentChatList.length > 0) {
                  ui.showMessage('Chats list updated.', false);
             } else if (!elements.chatListDiv.querySelector('p')) {
                 // If the list is empty but no "Nenhum chat" message is shown yet, show status briefly.
                 ui.showMessage('No chat found.', false);
             }
            console.log("Active Chat ID:", state.currentActiveChatId);

        } catch (error) {
            state.currentChatList = [];
            state.currentActiveChatId = null;
            ui.renderChatList(); // Render empty state
            ui.showMessage(`Error retrieving data: ${error.message}`, true);
        }
    }

    /** Handles creating a new chat. */
    async function handleCreateChat() {
        const description = elements.chatDescriptionInput?.value.trim(); // Use optional chaining
        const mode = elements.chatModeSelectCreate?.value;
        if (mode === undefined) { // Check if element exists via value
             ui.showMessage("Erro: Elemento de modo não encontrado.", true); return;
        }
        ui.showMessage(`Creating chat (Mode: ${mode})...`, false);
        try {
            const newChatData = await api.createChat(description, mode);
            ui.showMessage(`Chat "${description || newChatData.chat_id}" (Mode: ${mode}) created. ID: ${newChatData.chat_id}`, false);
            ui.clearCreateForm();
            await refreshChatData();
        } catch (error) {
            ui.showMessage(`Erro ao criar chat: ${error.message}`, true);
        }
    }

    /** Handles clicks within the chat list table body (Event Delegation). */
    async function handleTableClick(event) {
        const target = event.target;
        const actionButton = target.closest('button[data-action]');

        if (!actionButton) return;

        const row = actionButton.closest('tr');
        const chatId = row?.dataset.chatId; // Get ID from row
        const action = actionButton.dataset.action;

        if (!chatId || !action) return;

        console.log(`Table Click - Action: ${action}, Chat ID: ${chatId}`);

        if (action === 'activate') {
            ui.showMessage(`Definindo chat ${chatId} como ativo...`, false);
            try {
                const result = await api.setActiveChat(chatId);
                ui.showMessage(result.message || `Chat ${chatId} agora está ativo.`, false);
                await refreshChatData();
            } catch (error) {
                ui.showMessage(`Erro ao ativar chat ${chatId}: ${error.message}`, true);
            }
        } else if (action === 'deactivate') {
             ui.showMessage(`Desativando chat ativo...`, false);
            try {
                 const result = await api.deactivateChat();
                 ui.showMessage(result.message || `Chat ativo desativado.`, false);
                 await refreshChatData();
            } catch (error) {
                 ui.showMessage(`Erro ao desativar chat: ${error.message}`, true);
            }
        } else if (action === 'delete') {
            const chatDesc = row.dataset.chatDesc || chatId; // Get desc from row
            if (!confirm(`Deletar chat "${chatDesc}" (ID: ${chatId})?`)) return;
            ui.showMessage(`Deletando chat ${chatId}...`, false);
            try {
                await api.deleteChat(chatId);
                ui.showMessage(`Chat ${chatId} deletado.`, false);
                await refreshChatData();
            } catch (error) {
                ui.showMessage(`Erro ao deletar chat ${chatId}: ${error.message}`, true);
            }
        }
    }

     /** Handles mode changes within the chat list table body (Event Delegation). */
    async function handleTableModeChange(event) {
        const target = event.target;

        if (!target.matches('select.mode-select')) return; // Target the select directly

        const selectElement = target;
        const row = selectElement.closest('tr');
        const chatId = row?.dataset.chatId; // Get ID from row
        const newMode = selectElement.value;

        if (!chatId) return;

        console.log(`Table Mode Change - Chat ID: ${chatId}, New Mode: ${newMode}`);

         ui.showMessage(`Atualizando modo do chat ${chatId} para ${newMode}...`, false);
        try {
            const result = await api.updateChatMode(chatId, newMode);
            ui.showMessage(result.message || `Modo do chat ${chatId} atualizado para ${newMode}.`, false);
            await refreshChatData(); // Refresh to ensure UI consistency
        } catch (error) {
             ui.showMessage(`Erro ao atualizar modo do chat ${chatId}: ${error.message}`, true);
             // Revert UI optimistically on error? Or let refresh handle it?
             // For simplicity, let refresh handle visual state.
             await refreshChatData(); // Refresh even on error to show actual state
        }
    }


    // --- Event Listeners Setup ---
    function setupEventListeners() {
        // Static element listeners
        elements.btnRefreshList?.addEventListener('click', refreshChatData);
        elements.btnCreateChat?.addEventListener('click', handleCreateChat);

        // Event Delegation listeners on the container div
        elements.chatListDiv?.addEventListener('click', handleTableClick);
        elements.chatListDiv?.addEventListener('change', handleTableModeChange);
    }

    // --- Initialization ---
    function initialize() {
        console.log("Initializing Chat Manager...");
        ui.populateCreateModeSelect();
        setupEventListeners();
        refreshChatData(); // Load initial data
        console.log("Chat Manager Initialized.");
    }

    initialize(); // Start

}); // End DOMContentLoaded
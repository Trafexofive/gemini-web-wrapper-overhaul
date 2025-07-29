import { useAuthStore } from '@/store/auth-store'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public status: number,
    public statusText: string
  ) {
    super(message)
    this.name = 'ApiRequestError'
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const { token } = useAuthStore.getState()
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  }

  // Add authorization header if token exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new ApiRequestError(
      errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
      response.status,
      response.statusText
    )
  }

  return response.json()
}

// Types
export interface ChatInfo {
  chat_id: string
  description: string | null
  mode: string | null
}

export interface CreateChatRequest {
  description?: string
  mode?: string
}

export interface ChatCompletionRequest {
  model?: string
  messages: Array<{
    role: 'user' | 'assistant' | 'system'
    content: string
    name?: string
  }>
  temperature?: number
}

export interface ChatCompletionResponse {
  id: string
  object: string
  created: number
  model: string
  choices: Array<{
    index: number
    message: {
      role: string
      content: string
      name: string | null
    }
    finish_reason: string | null
  }>
  usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
  system_fingerprint: string | null
  chat_id: string
}

export const api = {
  // Chat management
  async getChats(): Promise<ChatInfo[]> {
    return apiRequest<ChatInfo[]>('/chats/')
  },

  async createChat(data: CreateChatRequest): Promise<string> {
    const response = await apiRequest<{ chat_id: string }>('/chats/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    return response.chat_id
  },

  async setActiveChat(chatId: string): Promise<void> {
    await apiRequest('/chats/active', {
      method: 'POST',
      body: JSON.stringify({ chat_id: chatId }),
    })
  },

  async getActiveChat(): Promise<{ active_chat_id: string | null }> {
    return apiRequest<{ active_chat_id: string | null }>('/chats/active')
  },

  async updateChatMode(chatId: string, mode: string): Promise<void> {
    await apiRequest(`/chats/${chatId}/mode`, {
      method: 'PUT',
      body: JSON.stringify({ mode }),
    })
  },

  async deleteChat(chatId: string): Promise<void> {
    await apiRequest(`/chats/${chatId}`, {
      method: 'DELETE',
    })
  },

  // Chat completions
  async sendMessage(data: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    return apiRequest<ChatCompletionResponse>('/chats/completions', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return apiRequest<{ status: string }>('/health')
  },
}

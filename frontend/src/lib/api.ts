import { 
  ChatInfo, 
  CreateChatRequest, 
  UpdateChatModeRequest, 
  SetActiveChatRequest, 
  GetActiveChatResponse,
  ChatCompletionRequest,
  ChatCompletionResponse
} from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api'

class ApiRequestError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiRequestError'
  }
}

async function apiRequest<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new ApiRequestError(response.status, errorData.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export const api = {
  // Chat management
  async getChats(): Promise<ChatInfo[]> {
    return apiRequest<ChatInfo[]>('/chats')
  },

  async createChat(data: CreateChatRequest): Promise<string> {
    return apiRequest<string>('/chats', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async deleteChat(chatId: string): Promise<void> {
    return apiRequest<void>(`/chats/${chatId}`, {
      method: 'DELETE',
    })
  },

  async updateChatMode(chatId: string, data: UpdateChatModeRequest): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(`/chats/${chatId}/mode`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  // Active chat management
  async getActiveChat(): Promise<GetActiveChatResponse> {
    return apiRequest<GetActiveChatResponse>('/chats/active')
  },

  async setActiveChat(data: SetActiveChatRequest): Promise<{ message: string }> {
    return apiRequest<{ message: string }>('/chats/active', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  // Chat completions
  async sendMessage(data: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    return apiRequest<ChatCompletionResponse>('/chat/completions', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return apiRequest<{ status: string }>('/health')
  },
}
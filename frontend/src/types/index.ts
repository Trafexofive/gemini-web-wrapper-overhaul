export interface ChatInfo {
  chat_id: string
  description: string | null
  mode: string | null
}

export interface CreateChatRequest {
  description?: string
  mode?: string
}

export interface UpdateChatModeRequest {
  mode: string
}

export interface SetActiveChatRequest {
  chat_id?: string | null
}

export interface GetActiveChatResponse {
  active_chat_id: string | null
}

export interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  name?: string
}

export interface ChatCompletionRequest {
  messages: Message[]
  model?: string
  temperature?: number
  max_tokens?: number
  stream?: boolean
}

export interface ChatCompletionResponse {
  id: string
  object: string
  created: number
  model: string
  choices: Array<{
    index: number
    message: Message
    finish_reason?: string
  }>
  usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
  chat_id: string
}

export interface ChatSession {
  id: string
  description: string
  mode: string
  messages: Message[]
  isActive: boolean
  createdAt: Date
  updatedAt: Date
}

export type ChatMode = 'Default' | 'Code' | 'Architect' | 'Debug' | 'Ask'

export interface ApiError {
  detail: string
  status_code: number
}
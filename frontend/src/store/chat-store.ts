import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { 
  ChatInfo, 
  Message, 
  ChatMode,
  CreateChatRequest,
  UpdateChatModeRequest 
} from '@/types'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

interface ChatState {
  // State
  chats: ChatInfo[]
  activeChatId: string | null
  messages: Record<string, Message[]>
  isLoading: boolean
  isSending: boolean
  
  // Actions
  loadChats: () => Promise<void>
  createChat: (data: CreateChatRequest) => Promise<void>
  deleteChat: (chatId: string) => Promise<void>
  setActiveChat: (chatId: string | null) => Promise<void>
  updateChatMode: (chatId: string, mode: ChatMode) => Promise<void>
  sendMessage: (content: string) => Promise<void>
  addMessage: (chatId: string, message: Message) => void
  clearMessages: (chatId: string) => void
  getActiveChat: () => ChatInfo | null
  getChatMessages: (chatId: string) => Message[]
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set, get) => ({
      // Initial state
      chats: [],
      activeChatId: null,
      messages: {},
      isLoading: false,
      isSending: false,

      // Load all chats
      loadChats: async () => {
        set({ isLoading: true })
        try {
          const chats = await api.getChats()
          set({ chats })
          
          // Load active chat
          const activeChat = await api.getActiveChat()
          set({ activeChatId: activeChat.active_chat_id })
        } catch (error) {
          console.error('Failed to load chats:', error)
          toast.error('Failed to load chats')
        } finally {
          set({ isLoading: false })
        }
      },

      // Create new chat
      createChat: async (data: CreateChatRequest) => {
        try {
          const chatId = await api.createChat(data)
          await get().loadChats() // Reload chats
          toast.success('Chat created successfully')
          
          // Set as active if it's the first chat
          if (get().chats.length === 0) {
            await get().setActiveChat(chatId)
          }
        } catch (error) {
          console.error('Failed to create chat:', error)
          toast.error('Failed to create chat')
        }
      },

      // Delete chat
      deleteChat: async (chatId: string) => {
        try {
          await api.deleteChat(chatId)
          
          // Remove from state
          set(state => {
            const { [chatId]: removed, ...remainingMessages } = state.messages
            return {
              chats: state.chats.filter(chat => chat.chat_id !== chatId),
              messages: remainingMessages
            }
          })
          
          // If this was the active chat, clear active
          if (get().activeChatId === chatId) {
            set({ activeChatId: null })
          }
          
          toast.success('Chat deleted successfully')
        } catch (error) {
          console.error('Failed to delete chat:', error)
          toast.error('Failed to delete chat')
        }
      },

      // Set active chat
      setActiveChat: async (chatId: string | null) => {
        try {
          await api.setActiveChat(chatId || '')
          set({ activeChatId: chatId })
          
          if (chatId) {
            toast.success('Chat activated')
          } else {
            toast.success('Chat deactivated')
          }
        } catch (error) {
          console.error('Failed to set active chat:', error)
          toast.error('Failed to set active chat')
        }
      },

      // Update chat mode
      updateChatMode: async (chatId: string, mode: ChatMode) => {
        try {
          await api.updateChatMode(chatId, mode)
          
          // Update in state
          set(state => ({
            chats: state.chats.map(chat => 
              chat.chat_id === chatId ? { ...chat, mode } : chat
            )
          }))
          
          toast.success(`Mode updated to ${mode}`)
        } catch (error) {
          console.error('Failed to update chat mode:', error)
          toast.error('Failed to update chat mode')
        }
      },

      // Send message
      sendMessage: async (content: string) => {
        const { activeChatId } = get()
        if (!activeChatId) {
          toast.error('No active chat selected')
          return
        }

        set({ isSending: true })
        
        try {
          // Add user message immediately
          const userMessage: Message = {
            role: 'user',
            content,
          }
          get().addMessage(activeChatId, userMessage)

          // Send to API
          const response = await api.sendMessage({
            messages: [userMessage]
          })

          // Add assistant response
          const assistantMessage: Message = {
            role: response.choices[0].message.role as 'user' | 'assistant' | 'system',
            content: response.choices[0].message.content,
          }
          get().addMessage(activeChatId, assistantMessage)
          
        } catch (error) {
          console.error('Failed to send message:', error)
          toast.error('Failed to send message')
          
          // Remove the user message on error
          set(state => ({
            messages: {
              ...state.messages,
              [activeChatId]: state.messages[activeChatId]?.slice(0, -1) || []
            }
          }))
        } finally {
          set({ isSending: false })
        }
      },

      // Add message to chat
      addMessage: (chatId: string, message: Message) => {
        set(state => ({
          messages: {
            ...state.messages,
            [chatId]: [...(state.messages[chatId] || []), message]
          }
        }))
      },

      // Clear messages for a chat
      clearMessages: (chatId: string) => {
        set(state => ({
          messages: {
            ...state.messages,
            [chatId]: []
          }
        }))
      },

      // Get active chat info
      getActiveChat: () => {
        const { chats, activeChatId } = get()
        return chats.find(chat => chat.chat_id === activeChatId) || null
      },

      // Get messages for a chat
      getChatMessages: (chatId: string) => {
        return get().messages[chatId] || []
      },
    }),
    {
      name: 'chat-store',
    }
  )
)
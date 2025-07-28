'use client'

import { useState } from 'react'
import { useChatStore } from '@/store/chat-store'
import { Button } from '@/components/ui/button'
import { CreateChatDialog } from './create-chat-dialog'
import { ChatModeDialog } from './chat-mode-dialog'
import { 
  Plus, 
  RefreshCw, 
  Trash2, 
  MessageSquare, 
  Settings,
  Sparkles
} from 'lucide-react'
import toast from 'react-hot-toast'

export function Sidebar() {
  const { 
    chats, 
    activeChatId, 
    loadChats, 
    deleteChat, 
    setActiveChat,
    isLoading 
  } = useChatStore()
  
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isModeDialogOpen, setIsModeDialogOpen] = useState(false)

  const handleRefresh = async () => {
    await loadChats()
    toast.success('Chats refreshed')
  }

  const handleDeleteChat = async (chatId: string) => {
    await deleteChat(chatId)
  }

  const handleSetActive = async (chatId: string) => {
    await setActiveChat(chatId)
  }

  return (
    <div className="w-80 bg-white/10 backdrop-blur-xl border-r border-white/20 flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-white/20">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Chat Sessions
          </h2>
          <Button
            onClick={() => setIsCreateDialogOpen(true)}
            size="sm"
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white"
          >
            <Plus className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="flex space-x-2">
          <Button
            onClick={handleRefresh}
            variant="ghost"
            size="sm"
            disabled={isLoading}
            className="flex-1 text-slate-300 hover:text-white hover:bg-white/10"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            onClick={() => setIsModeDialogOpen(true)}
            variant="ghost"
            size="sm"
            className="text-slate-300 hover:text-white hover:bg-white/10"
          >
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto p-4">
        {chats.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-8 h-8 text-purple-400" />
            </div>
            <p className="text-slate-400 mb-2">No chats yet</p>
            <Button
              onClick={() => setIsCreateDialogOpen(true)}
              variant="outline"
              size="sm"
              className="border-white/20 text-white hover:bg-white/10"
            >
              Create your first chat
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            {chats.map((chat) => (
              <div
                key={chat.chat_id}
                className={`group relative p-3 rounded-xl border transition-all duration-200 cursor-pointer ${
                  activeChatId === chat.chat_id
                    ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-purple-500/50'
                    : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                }`}
                onClick={() => handleSetActive(chat.chat_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${
                      activeChatId === chat.chat_id ? 'text-white' : 'text-slate-300'
                    }`}>
                      {chat.description || 'Untitled Chat'}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      {chat.mode || 'Default'}
                    </p>
                  </div>
                  
                  <Button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteChat(chat.chat_id)
                    }}
                    variant="ghost"
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all duration-200"
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/20">
        <div className="text-center">
          <p className="text-xs text-slate-500">
            Powered by Gemini AI
          </p>
        </div>
      </div>

      {/* Dialogs */}
      <CreateChatDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
      />
      <ChatModeDialog
        open={isModeDialogOpen}
        onOpenChange={setIsModeDialogOpen}
      />
    </div>
  )
}
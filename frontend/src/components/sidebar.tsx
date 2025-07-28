'use client'

import { useState } from 'react'
import { 
  Plus, 
  MessageSquare, 
  Settings, 
  Trash2, 
  Check,
  MoreHorizontal,
  Bot
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useChatStore } from '@/store/chat-store'
import { ChatMode } from '@/types'
import { cn } from '@/lib/utils'
import { CreateChatDialog } from './create-chat-dialog'
import { ChatModeDialog } from './chat-mode-dialog'

const CHAT_MODES: { value: ChatMode; label: string; description: string }[] = [
  { value: 'Default', label: 'Default', description: 'General conversation' },
  { value: 'Code', label: 'Code', description: 'Programming assistance' },
  { value: 'Architect', label: 'Architect', description: 'System design help' },
  { value: 'Debug', label: 'Debug', description: 'Troubleshooting support' },
  { value: 'Ask', label: 'Ask', description: 'Question answering' },
]

export function Sidebar() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isModeDialogOpen, setIsModeDialogOpen] = useState(false)
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null)
  
  const {
    chats,
    activeChatId,
    isLoading,
    setActiveChat,
    deleteChat,
    updateChatMode,
  } = useChatStore()

  const handleChatSelect = async (chatId: string) => {
    await setActiveChat(chatId)
  }

  const handleDeleteChat = async (chatId: string) => {
    if (confirm('Are you sure you want to delete this chat?')) {
      await deleteChat(chatId)
    }
  }

  const handleModeChange = async (chatId: string, mode: ChatMode) => {
    await updateChatMode(chatId, mode)
    setIsModeDialogOpen(false)
    setSelectedChatId(null)
  }

  return (
    <div className="w-80 border-r bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Gemini Chat
          </h1>
          <Button
            size="icon"
            variant="ghost"
            onClick={() => setIsCreateDialogOpen(true)}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-muted-foreground">
            Loading chats...
          </div>
        ) : chats.length === 0 ? (
          <div className="p-4 text-center text-muted-foreground">
            <MessageSquare className="mx-auto h-8 w-8 mb-2" />
            <p>No chats yet</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => setIsCreateDialogOpen(true)}
            >
              Create your first chat
            </Button>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {chats.map((chat) => (
              <ChatItem
                key={chat.chat_id}
                chat={chat}
                isActive={chat.chat_id === activeChatId}
                onSelect={() => handleChatSelect(chat.chat_id)}
                onDelete={() => handleDeleteChat(chat.chat_id)}
                onModeChange={() => {
                  setSelectedChatId(chat.chat_id)
                  setIsModeDialogOpen(true)
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create Chat Dialog */}
      <CreateChatDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        modes={CHAT_MODES}
      />

      {/* Chat Mode Dialog */}
      <ChatModeDialog
        open={isModeDialogOpen}
        onOpenChange={setIsModeDialogOpen}
        modes={CHAT_MODES}
        onModeSelect={(mode) => {
          if (selectedChatId) {
            handleModeChange(selectedChatId, mode)
          }
        }}
      />
    </div>
  )
}

interface ChatItemProps {
  chat: {
    chat_id: string
    description: string | null
    mode: string | null
  }
  isActive: boolean
  onSelect: () => void
  onDelete: () => void
  onModeChange: () => void
}

function ChatItem({ chat, isActive, onSelect, onDelete, onModeChange }: ChatItemProps) {
  const [showActions, setShowActions] = useState(false)

  return (
    <div
      className={cn(
        "group relative flex items-center space-x-3 rounded-lg p-3 cursor-pointer transition-colors",
        isActive
          ? "bg-primary text-primary-foreground"
          : "hover:bg-muted"
      )}
      onClick={onSelect}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <MessageSquare className="h-4 w-4 flex-shrink-0" />
      
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">
          {chat.description || 'Untitled Chat'}
        </p>
        <p className={cn(
          "text-xs truncate",
          isActive ? "text-primary-foreground/70" : "text-muted-foreground"
        )}>
          {chat.mode || 'Default'}
        </p>
      </div>

      {showActions && (
        <div className="absolute right-2 flex items-center space-x-1">
          <Button
            size="icon"
            variant="ghost"
            className="h-6 w-6"
            onClick={(e) => {
              e.stopPropagation()
              onModeChange()
            }}
          >
            <Settings className="h-3 w-3" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-6 w-6"
            onClick={(e) => {
              e.stopPropagation()
              onDelete()
            }}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      )}

      {isActive && (
        <Check className="h-4 w-4 flex-shrink-0" />
      )}
    </div>
  )
}
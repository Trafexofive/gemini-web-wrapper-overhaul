'use client'

import { useState } from 'react'
import { useChatStore } from '@/store/chat-store'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Settings, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'

interface ChatModeDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ChatModeDialog({ open, onOpenChange }: ChatModeDialogProps) {
  const [selectedMode, setSelectedMode] = useState('Default')
  const { updateChatMode, activeChatId, isLoading } = useChatStore()

  const handleModeChange = async () => {
    if (!activeChatId) {
      toast.error('No active chat selected')
      return
    }

    try {
      await updateChatMode(activeChatId, selectedMode as any)
      onOpenChange(false)
      toast.success('Chat mode updated successfully!')
    } catch (error) {
      toast.error('Failed to update chat mode')
    }
  }

  const chatModes = [
    { 
      value: 'Default', 
      label: 'Default', 
      description: 'General conversation and assistance',
      icon: '💬'
    },
    { 
      value: 'Code', 
      label: 'Code', 
      description: 'Programming and development help',
      icon: '💻'
    },
    { 
      value: 'Architect', 
      label: 'Architect', 
      description: 'System design and architecture',
      icon: '🏗️'
    },
    { 
      value: 'Debug', 
      label: 'Debug', 
      description: 'Troubleshooting and problem solving',
      icon: '🐛'
    },
    { 
      value: 'Ask', 
      label: 'Ask', 
      description: 'Question answering and research',
      icon: '❓'
    },
  ]

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-white/10 backdrop-blur-xl border-white/20 text-white max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl font-bold">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <Settings className="w-4 h-4 text-white" />
            </div>
            Chat Mode Settings
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">
              Select Chat Mode
            </label>
            <div className="grid grid-cols-1 gap-3">
              {chatModes.map((mode) => (
                <button
                  key={mode.value}
                  type="button"
                  onClick={() => setSelectedMode(mode.value)}
                  className={`p-4 rounded-xl border text-left transition-all duration-200 ${
                    selectedMode === mode.value
                      ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-purple-500/50'
                      : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{mode.icon}</span>
                      <div>
                        <p className={`font-medium ${
                          selectedMode === mode.value ? 'text-white' : 'text-slate-300'
                        }`}>
                          {mode.label}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          {mode.description}
                        </p>
                      </div>
                    </div>
                    {selectedMode === mode.value && (
                      <div className="w-5 h-5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                        <div className="w-2.5 h-2.5 bg-white rounded-full" />
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="flex space-x-3 pt-4">
            <Button
              type="button"
              variant="ghost"
              onClick={() => onOpenChange(false)}
              className="flex-1 text-slate-400 hover:text-white hover:bg-white/10"
            >
              Cancel
            </Button>
            <Button
              onClick={handleModeChange}
              disabled={isLoading}
              className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Updating...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-4 h-4" />
                  <span>Update Mode</span>
                </div>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
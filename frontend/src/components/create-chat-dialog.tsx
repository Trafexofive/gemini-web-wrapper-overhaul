'use client'

import { useState } from 'react'
import { useChatStore } from '@/store/chat-store'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Sparkles, MessageSquare } from 'lucide-react'
import toast from 'react-hot-toast'

interface CreateChatDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CreateChatDialog({ open, onOpenChange }: CreateChatDialogProps) {
  const [description, setDescription] = useState('')
  const [mode, setMode] = useState('Default')
  const { createChat, isLoading } = useChatStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!description.trim()) {
      toast.error('Please enter a description')
      return
    }

    try {
      await createChat({
        description: description.trim() || undefined,
        mode: mode as any
      })
      setDescription('')
      setMode('Default')
      onOpenChange(false)
      toast.success('Chat created successfully!')
    } catch (error) {
      toast.error('Failed to create chat')
    }
  }

  const chatModes = [
    { value: 'Default', label: 'Default', description: 'General conversation' },
    { value: 'Code', label: 'Code', description: 'Programming assistance' },
    { value: 'Architect', label: 'Architect', description: 'System design help' },
    { value: 'Debug', label: 'Debug', description: 'Troubleshooting support' },
    { value: 'Ask', label: 'Ask', description: 'Question answering' },
  ]

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-white/10 backdrop-blur-xl border-white/20 text-white max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl font-bold">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <MessageSquare className="w-4 h-4 text-white" />
            </div>
            Create New Chat
          </DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">
              Description
            </label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter a description for your chat..."
              className="bg-white/10 border-white/20 text-white placeholder:text-slate-400 focus:border-purple-500 focus:ring-purple-500"
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">
              Chat Mode
            </label>
            <div className="grid grid-cols-1 gap-2">
              {chatModes.map((chatMode) => (
                <button
                  key={chatMode.value}
                  type="button"
                  onClick={() => setMode(chatMode.value)}
                  className={`p-3 rounded-xl border text-left transition-all duration-200 ${
                    mode === chatMode.value
                      ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-purple-500/50'
                      : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className={`font-medium ${
                        mode === chatMode.value ? 'text-white' : 'text-slate-300'
                      }`}>
                        {chatMode.label}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        {chatMode.description}
                      </p>
                    </div>
                    {mode === chatMode.value && (
                      <div className="w-4 h-4 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-white rounded-full" />
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
              type="submit"
              disabled={!description.trim() || isLoading}
              className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Creating...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-4 h-4" />
                  <span>Create Chat</span>
                </div>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useChatStore } from '@/store/chat-store'
import { ChatMode } from '@/types'

interface CreateChatDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  modes: { value: ChatMode; label: string; description: string }[]
}

export function CreateChatDialog({ open, onOpenChange, modes }: CreateChatDialogProps) {
  const [description, setDescription] = useState('')
  const [selectedMode, setSelectedMode] = useState<ChatMode>('Default')
  const [isCreating, setIsCreating] = useState(false)
  
  const { createChat } = useChatStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isCreating) return

    setIsCreating(true)
    try {
      await createChat({
        description: description.trim() || undefined,
        mode: selectedMode,
      })
      setDescription('')
      setSelectedMode('Default')
      onOpenChange(false)
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New Chat</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium">
              Description (optional)
            </label>
            <Input
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter chat description..."
              maxLength={255}
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium">Chat Mode</label>
            <div className="grid grid-cols-1 gap-2">
              {modes.map((mode) => (
                <button
                  key={mode.value}
                  type="button"
                  onClick={() => setSelectedMode(mode.value)}
                  className={`p-3 text-left rounded-lg border transition-colors ${
                    selectedMode === mode.value
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted'
                  }`}
                >
                  <div className="font-medium">{mode.label}</div>
                  <div className="text-sm text-muted-foreground">
                    {mode.description}
                  </div>
                </button>
              ))}
            </div>
          </div>
          
          <div className="flex justify-end space-x-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isCreating}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isCreating}>
              {isCreating ? 'Creating...' : 'Create Chat'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
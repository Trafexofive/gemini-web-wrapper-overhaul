'use client'

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { ChatMode } from '@/types'

interface ChatModeDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  modes: { value: ChatMode; label: string; description: string }[]
  onModeSelect: (mode: ChatMode) => void
}

export function ChatModeDialog({ open, onOpenChange, modes, onModeSelect }: ChatModeDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Change Chat Mode</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Select a mode to change how Gemini responds in this chat.
          </p>
          
          <div className="grid grid-cols-1 gap-2">
            {modes.map((mode) => (
              <button
                key={mode.value}
                type="button"
                onClick={() => onModeSelect(mode.value)}
                className="p-3 text-left rounded-lg border border-border hover:bg-muted transition-colors"
              >
                <div className="font-medium">{mode.label}</div>
                <div className="text-sm text-muted-foreground">
                  {mode.description}
                </div>
              </button>
            ))}
          </div>
          
          <div className="flex justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
'use client'

import { useEffect } from 'react'
import { ChatInterface } from '@/components/chat-interface'
import { Sidebar } from '@/components/sidebar'
import { useChatStore } from '@/store/chat-store'

export default function Home() {
  const { loadChats } = useChatStore()

  useEffect(() => {
    loadChats()
  }, [loadChats])

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <ChatInterface />
    </div>
  )
}
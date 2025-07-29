'use client'

import { useEffect } from 'react'
import { ChatInterface } from '@/components/chat-interface'
import { Sidebar } from '@/components/sidebar'
import { AuthGuard } from '@/components/auth-guard'
import { useChatStore } from '@/store/chat-store'
import { useAuthStore } from '@/store/auth-store'
import { LogOut, User, Key } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { FullScreenLoading } from '@/components/loading-spinner'

export default function Home() {
  const { loadChats } = useChatStore()
  const { user, logout, checkAuth, isInitialized } = useAuthStore()

  useEffect(() => {
    // Only load chats if auth is initialized and user is authenticated
    if (isInitialized && user) {
      loadChats()
    }
  }, [isInitialized, user, loadChats])

  // Show loading while auth is being initialized
  if (!isInitialized) {
    return <FullScreenLoading text="Initializing..." />
  }

  return (
    <AuthGuard>
      <div className="flex h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 z-50 bg-white/10 backdrop-blur-xl border-b border-white/20">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">G</span>
              </div>
              <h1 className="text-xl font-bold text-white">Gemini Chat</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-white">{user?.username}</p>
                  <p className="text-xs text-slate-400">{user?.email}</p>
                </div>
              </div>
              <Link href="/api-keys">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-slate-400 hover:text-white hover:bg-white/10"
                >
                  <Key className="w-4 h-4" />
                </Button>
              </Link>
              <Button
                onClick={logout}
                variant="ghost"
                size="sm"
                className="text-slate-400 hover:text-white hover:bg-white/10"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex w-full pt-20">
          <Sidebar />
          <ChatInterface />
        </div>
      </div>
    </AuthGuard>
  )
}
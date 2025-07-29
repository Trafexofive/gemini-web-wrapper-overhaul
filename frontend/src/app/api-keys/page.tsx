'use client'

import { useEffect, useState } from 'react'
import { useAuthStore } from '@/store/auth-store'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Plus, Trash2, Copy, Check } from 'lucide-react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

interface APIKey {
  id: string
  name: string
  key: string
  created_at: string
  last_used?: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'

export default function APIKeysPage() {
  const { token, user } = useAuthStore()
  const router = useRouter()
  const [apiKeys, setApiKeys] = useState<APIKey[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  useEffect(() => {
    loadAPIKeys()
  }, [])

  const loadAPIKeys = async () => {
    if (!token) return

    try {
      const response = await fetch(`${API_BASE}/auth/api-keys`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to load API keys')
      }

      const data = await response.json()
      setApiKeys(data.keys || [])
    } catch (error) {
      toast.error('Failed to load API keys')
      console.error('Error loading API keys:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const createAPIKey = async () => {
    if (!token || !newKeyName.trim()) return

    setIsCreating(true)
    try {
      const response = await fetch(`${API_BASE}/auth/api-keys`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: newKeyName.trim() }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create API key')
      }

      const newKey = await response.json()
      setApiKeys(prev => [newKey, ...prev])
      setNewKeyName('')
      toast.success('API key created successfully!')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create API key'
      toast.error(errorMessage)
    } finally {
      setIsCreating(false)
    }
  }

  const deleteAPIKey = async (keyId: string) => {
    if (!token) return

    try {
      const response = await fetch(`${API_BASE}/auth/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to delete API key')
      }

      setApiKeys(prev => prev.filter(key => key.id !== keyId))
      toast.success('API key deleted successfully!')
    } catch (error) {
      toast.error('Failed to delete API key')
      console.error('Error deleting API key:', error)
    }
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedKey(text)
      toast.success('API key copied to clipboard!')
      setTimeout(() => setCopiedKey(null), 2000)
    } catch (error) {
      toast.error('Failed to copy API key')
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="bg-white/10 backdrop-blur-xl border-b border-white/20">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center space-x-4">
            <Button
              onClick={() => router.push('/')}
              variant="ghost"
              size="sm"
              className="text-slate-400 hover:text-white hover:bg-white/10"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <h1 className="text-xl font-bold text-white">API Keys</h1>
          </div>
          
          <div className="text-right">
            <p className="text-sm font-medium text-white">{user?.username}</p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <Card className="bg-white/10 backdrop-blur-xl border-white/20">
            <CardHeader>
              <CardTitle className="text-white">Create New API Key</CardTitle>
              <CardDescription className="text-slate-300">
                Create a new API key to access the Gemini API programmatically
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex space-x-4">
                <Input
                  placeholder="Enter API key name"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  className="flex-1 bg-white/10 border-white/20 text-white placeholder:text-slate-400"
                />
                <Button
                  onClick={createAPIKey}
                  disabled={!newKeyName.trim() || isCreating}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                >
                  {isCreating ? 'Creating...' : 'Create'}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-xl border-white/20">
            <CardHeader>
              <CardTitle className="text-white">Your API Keys</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="text-center py-8">
                  <p className="text-slate-400">Loading...</p>
                </div>
              ) : apiKeys.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-slate-400">No API keys found.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {apiKeys.map((key) => (
                    <div
                      key={key.id}
                      className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10"
                    >
                      <div className="flex-1">
                        <h3 className="font-medium text-white">{key.name}</h3>
                        <p className="text-xs text-slate-400 mt-1">
                          Created: {formatDate(key.created_at)}
                        </p>
                      </div>
                      <Button
                        onClick={() => deleteAPIKey(key.id)}
                        variant="ghost"
                        size="sm"
                        className="text-red-400 hover:text-red-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
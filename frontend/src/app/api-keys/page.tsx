'use client'

import { useEffect, useState } from 'react'
import { useAuthStore } from '@/store/auth-store'
import { AuthGuard } from '@/components/auth-guard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Plus, Trash2, Copy, Check, Eye, EyeOff } from 'lucide-react'
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
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<{ id: string; key: string; name: string } | null>(null)

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
      
      // Store the newly created key for display
      setNewlyCreatedKey({
        id: newKey.id,
        key: newKey.key,
        name: newKey.name
      })
      
      toast.success('API key created successfully! Copy it now - it won\'t be shown again!')
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

  const toggleKeyVisibility = (keyId: string) => {
    setShowKeys(prev => ({
      ...prev,
      [keyId]: !prev[keyId]
    }))
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
    <AuthGuard>
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
            {/* Newly Created Key Display */}
            {newlyCreatedKey && (
              <Card className="bg-green-500/10 backdrop-blur-xl border-green-500/20">
                <CardHeader>
                  <CardTitle className="text-green-400">New API Key Created!</CardTitle>
                  <CardDescription className="text-green-300">
                    Copy this key now - it won't be shown again!
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm text-green-300 mb-2">Name: {newlyCreatedKey.name}</p>
                      <div className="flex items-center space-x-2">
                        <code className="flex-1 bg-black/20 p-3 rounded text-green-400 text-sm font-mono break-all">
                          {newlyCreatedKey.key}
                        </code>
                        <Button
                          onClick={() => copyToClipboard(newlyCreatedKey.key)}
                          size="sm"
                          className="bg-green-500 hover:bg-green-600"
                        >
                          {copiedKey === newlyCreatedKey.key ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                        </Button>
                      </div>
                    </div>
                    <Button
                      onClick={() => setNewlyCreatedKey(null)}
                      variant="outline"
                      className="border-green-500/20 text-green-400 hover:bg-green-500/10"
                    >
                      Dismiss
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

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
                <CardDescription className="text-slate-300">
                  Click the eye icon to reveal and copy your API keys
                </CardDescription>
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
                        className="p-4 bg-white/5 rounded-lg border border-white/10"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h3 className="font-medium text-white">{key.name}</h3>
                            <p className="text-xs text-slate-400">
                              Created: {formatDate(key.created_at)}
                            </p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Button
                              onClick={() => toggleKeyVisibility(key.id)}
                              variant="ghost"
                              size="sm"
                              className="text-slate-400 hover:text-white"
                            >
                              {showKeys[key.id] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </Button>
                            {showKeys[key.id] && (
                              <Button
                                onClick={() => copyToClipboard(key.key)}
                                variant="ghost"
                                size="sm"
                                className="text-green-400 hover:text-green-300"
                              >
                                {copiedKey === key.key ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                              </Button>
                            )}
                            <Button
                              onClick={() => deleteAPIKey(key.id)}
                              variant="ghost"
                              size="sm"
                              className="text-red-400 hover:text-red-300"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                        {showKeys[key.id] && (
                          <div className="mt-3">
                            <code className="block w-full bg-black/20 p-3 rounded text-green-400 text-sm font-mono break-all">
                              {key.key}
                            </code>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AuthGuard>
  )
}
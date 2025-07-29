import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import toast from 'react-hot-toast'

interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  created_at: string
  updated_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  isInitialized: boolean
  
  // Actions
  login: (email: string, password: string) => Promise<boolean>
  register: (email: string, password: string, username: string) => Promise<boolean>
  logout: () => void
  setUser: (user: User) => void
  setToken: (token: string) => void
  clearAuth: () => void
  checkAuth: () => Promise<boolean>
  initialize: () => Promise<void>
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      isInitialized: false,

      initialize: async () => {
        const { token } = get()
        if (!token) {
          set({ isInitialized: true })
          return
        }

        try {
          const response = await fetch(`${API_BASE}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          })

          if (response.ok) {
            const user = await response.json()
            set({ 
              user, 
              isAuthenticated: true, 
              isInitialized: true 
            })
          } else {
            set({ 
              user: null, 
              token: null, 
              isAuthenticated: false, 
              isInitialized: true 
            })
          }
        } catch (error) {
          console.error('Auth initialization failed:', error)
          set({ 
            user: null, 
            token: null, 
            isAuthenticated: false, 
            isInitialized: true 
          })
        }
      },

      login: async (email: string, password: string) => {
        set({ isLoading: true })
        
        try {
          const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
          })

          if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Login failed')
          }

          const data = await response.json()
          
          set({
            user: data.user,
            token: data.access_token,
            isAuthenticated: true,
            isLoading: false
          })
          
          toast.success('Successfully logged in!')
          return true
        } catch (error) {
          set({ isLoading: false })
          const errorMessage = error instanceof Error ? error.message : 'Login failed. Please try again.'
          toast.error(errorMessage)
          return false
        }
      },

      register: async (email: string, password: string, username: string) => {
        set({ isLoading: true })
        
        try {
          const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password, username }),
          })

          if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Registration failed')
          }

          const data = await response.json()
          
          set({
            user: data.user,
            token: data.access_token,
            isAuthenticated: true,
            isLoading: false
          })
          
          toast.success('Account created successfully!')
          return true
        } catch (error) {
          set({ isLoading: false })
          const errorMessage = error instanceof Error ? error.message : 'Registration failed. Please try again.'
          toast.error(errorMessage)
          return false
        }
      },

      logout: () => {
        get().clearAuth()
        toast.success('Logged out successfully')
      },

      setUser: (user: User) => {
        set({ user, isAuthenticated: true })
      },

      setToken: (token: string) => {
        set({ token })
      },

      clearAuth: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false
        })
      },

      checkAuth: async () => {
        const { token, isInitialized } = get()
        
        if (!isInitialized) {
          await get().initialize()
        }
        
        if (!token) {
          return false
        }

        try {
          const response = await fetch(`${API_BASE}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          })

          if (!response.ok) {
            get().clearAuth()
            return false
          }

          const user = await response.json()
          set({ user, isAuthenticated: true })
          return true
        } catch (error) {
          get().clearAuth()
          return false
        }
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
)
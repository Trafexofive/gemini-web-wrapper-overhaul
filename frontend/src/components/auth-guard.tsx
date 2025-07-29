'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/auth-store'
import { FullScreenLoading } from './loading-spinner'

interface AuthGuardProps {
  children: React.ReactNode
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading, isInitialized, checkAuth } = useAuthStore()
  const router = useRouter()
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    const verifyAuth = async () => {
      try {
        await checkAuth()
      } catch (error) {
        console.error('Auth check failed:', error)
      } finally {
        setIsChecking(false)
      }
    }

    // Only check auth if not already initialized
    if (!isInitialized) {
      verifyAuth()
    } else {
      setIsChecking(false)
    }
  }, [checkAuth, isInitialized])

  useEffect(() => {
    if (!isChecking && !isAuthenticated && isInitialized) {
      router.push('/login')
    }
  }, [isChecking, isAuthenticated, isInitialized, router])

  // Show loading while checking auth or if auth is being initialized
  if (isChecking || isLoading || !isInitialized) {
    return <FullScreenLoading text={!isInitialized ? 'Initializing...' : 'Loading...'} />
  }

  // Show loading if not authenticated (will redirect)
  if (!isAuthenticated) {
    return <FullScreenLoading text="Redirecting to login..." />
  }

  return <>{children}</>
}
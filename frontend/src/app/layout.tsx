import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from 'react-hot-toast'
import { ErrorBoundary } from '@/components/error-boundary'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Gemini Web Wrapper',
  description: 'A modern interface for the Gemini Web Wrapper API',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
        <Toaster position="top-right" />
      </body>
    </html>
  )
}
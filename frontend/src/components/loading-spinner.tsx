import { cn } from '@/lib/utils'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  className?: string
}

export function LoadingSpinner({ size = 'md', text, className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  }

  return (
    <div className={cn('flex flex-col items-center justify-center', className)}>
      <div className={cn(
        'border-2 border-purple-500 border-t-transparent rounded-full animate-spin',
        sizeClasses[size]
      )} />
      {text && (
        <p className="text-slate-400 mt-2 text-sm">{text}</p>
      )}
    </div>
  )
}

export function FullScreenLoading({ text = 'Loading...' }: { text?: string }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <LoadingSpinner size="lg" text={text} />
    </div>
  )
}
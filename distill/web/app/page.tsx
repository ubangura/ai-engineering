'use client'

import { Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL ?? ''

interface ErrorDetail {
  code: string
  detail: string
  retry_after_seconds?: number
}

export default function HomePage() {
  const router = useRouter()
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<ErrorDetail | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API}/api/video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ url }),
      })

      const data = await response.json()

      if (response.status === 200) {
        // Cache hit - redirect directly
        router.push(`/v?id=${data.video_id}`)
      } else if (response.status === 202) {
        // Processing - redirect with job ID
        router.push(`/v?id=${data.video_id}&job=${data.job_id}`)
      } else {
        // Error
        setError(data.detail)
      }
    } catch {
      setError({ code: 'network_error', detail: 'Failed to connect to the server. Please try again.' })
    } finally {
      setIsLoading(false)
    }
  }

  const formatRetryTime = (seconds: number) => {
    const minutes = Math.ceil(seconds / 60)
    return `Try again in ${minutes} minute${minutes !== 1 ? 's' : ''}.`
  }

  return (
    <main className="min-h-screen bg-background flex items-center justify-center px-4">
      {/* Vignette overlay */}
      <div 
        className="fixed inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 0%, rgba(28, 20, 16, 0.06) 100%)',
        }}
      />
      
      <div className="relative z-10 w-full max-w-xl text-center">
        {/* Heading */}
        <h1 
          className="text-6xl font-[800] text-text tracking-tight animate-fade-up"
          style={{ animationDelay: '0ms' }}
        >
          Distill
        </h1>
        
        {/* Amber rule */}
        <div 
          className="w-16 h-0.5 bg-accent mx-auto mt-6 animate-fade-up"
          style={{ animationDelay: '100ms' }}
        />
        
        {/* Tagline */}
        <p 
          className="text-xl text-text-muted mt-6 animate-fade-up"
          style={{ animationDelay: '150ms' }}
        >
          Paste a lecture URL. Get a complete study environment.
        </p>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-10 space-y-4">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className="w-full px-4 py-3 rounded-lg bg-surface border border-border text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring transition-shadow animate-fade-up"
            style={{ animationDelay: '200ms' }}
            disabled={isLoading}
          />
          
          <button
            type="submit"
            disabled={isLoading || !url.trim()}
            className="w-full px-4 py-3 rounded-lg bg-accent text-white font-semibold hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 animate-fade-up"
            style={{ animationDelay: '300ms' }}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Processing...
              </>
            ) : (
              'Process'
            )}
          </button>
        </form>
        
        {/* Error card */}
        {error && (
          <div className="mt-6 p-4 bg-accent-light border-l-4 border-accent rounded-lg text-left animate-fade-up">
            <p className="text-text font-medium">{error.detail}</p>
            {error.code === 'rate_limited' && error.retry_after_seconds && (
              <p className="text-text-muted mt-1">{formatRetryTime(error.retry_after_seconds)}</p>
            )}
          </div>
        )}
      </div>
    </main>
  )
}

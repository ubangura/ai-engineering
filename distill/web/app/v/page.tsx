'use client'

import { useState, useEffect, useRef, useCallback, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { 
  ChevronLeft, 
  ChevronRight, 
  ChevronDown,
  Loader2,
  AlertCircle,
  Check,
  Circle,
  Send
} from 'lucide-react'

const API = process.env.NEXT_PUBLIC_API_URL ?? ''

// Types — mirror the FastAPI Pydantic models exactly
interface OutlineNode {
  id: string
  title: string
  start_ts: number
  end_ts: number
  level: 'chapter' | 'section' | 'topic'
  children: OutlineNode[]
}

interface Outline {
  video_id: string
  nodes: OutlineNode[]
  inferred_category: string
  is_lecture_confidence: number
  language_detected: string
  recommended_temperature: number
}

interface Citation {
  section_id: string
  start_ts: number
  end_ts: number
  quote: string
}

interface Flashcard {
  question: string
  answer: string
  section_id: string
  citations: Citation[]
}

type SummaryDepth = 'ninety_seconds' | 'five_minutes' | 'full'

interface Summary {
  depth: SummaryDepth
  text: string
  section_anchors: string[]
}

interface StudyPack {
  video_id: string
  outline: Outline
  summaries: Summary[]
  flashcards: Flashcard[]
}

interface ProcessingState {
  metadata: boolean
  transcript: boolean
  transcriptSource?: string
  outline: boolean
  studyPack: boolean
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  citations?: { timestamp: number; quote: string }[]
  isStreaming?: boolean
}

interface ErrorState {
  code: string
  detail: string
}

// Utility to format timestamp
function formatTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Error Boundary Component
function ErrorCard({ error, onRetry }: { error: ErrorState; onRetry: () => void }) {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="bg-accent-light border-l-4 border-accent rounded-lg p-6 max-w-md">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-6 h-6 text-accent flex-shrink-0 mt-0.5" />
          <div>
            <h2 className="font-semibold text-text">Something went wrong</h2>
            <p className="text-text-muted mt-1">{error.detail}</p>
            <button
              onClick={onRetry}
              className="mt-4 px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover transition-colors font-medium"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Processing Checklist Component
function ProcessingChecklist({ state }: { state: ProcessingState }) {
  const items = [
    { key: 'metadata', label: 'Metadata verified', done: state.metadata },
    { 
      key: 'transcript', 
      label: 'Transcript fetched', 
      done: state.transcript,
      badge: state.transcriptSource
    },
    { key: 'outline', label: 'Outline drafted', done: state.outline },
    { key: 'studyPack', label: 'Study pack assembled', done: state.studyPack },
  ]

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="bg-surface border border-border rounded-lg p-8 max-w-md w-full">
        <h2 className="text-2xl font-bold text-text mb-6">Processing your lecture...</h2>
        <ul className="space-y-4">
          {items.map((item) => (
            <li key={item.key} className="flex items-center gap-3">
              <div className={`w-5 h-5 rounded-full flex items-center justify-center transition-colors ${
                item.done ? 'bg-accent text-white' : 'border-2 border-border'
              }`}>
                {item.done ? (
                  <Check className="w-3 h-3" />
                ) : (
                  <Circle className="w-3 h-3 text-border" />
                )}
              </div>
              <span className={`${item.done ? 'text-text' : 'text-text-muted'}`}>
                {item.label}
              </span>
              {item.badge && item.done && (
                <span className="font-mono text-xs bg-surface-alt text-accent px-2 py-0.5 rounded">
                  {item.badge}
                </span>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

// Outline Tree Component
function OutlineTree({ 
  nodes, 
  onSeek, 
  level = 0 
}: { 
  nodes: OutlineNode[]
  onSeek: (ts: number) => void
  level?: number 
}) {
  return (
    <ul className={`space-y-1 ${level > 0 ? 'ml-4 border-l border-border pl-4' : ''}`}>
      {nodes.map((node, index) => (
        <motion.li
          key={`${node.title}-${index}`}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.03 }}
        >
          <button
            onClick={() => onSeek(node.start_ts)}
            className="w-full text-left py-1.5 px-2 rounded hover:bg-surface-alt transition-colors group"
          >
            <span className="text-sm text-text group-hover:text-accent transition-colors">
              {node.title}
            </span>
            <span className="font-mono text-xs bg-surface-alt text-accent px-1.5 py-0.5 rounded ml-2">
              {formatTimestamp(node.start_ts)}
            </span>
          </button>
          {node.children && node.children.length > 0 && (
            <OutlineTree nodes={node.children} onSeek={onSeek} level={level + 1} />
          )}
        </motion.li>
      ))}
    </ul>
  )
}

function MarkdownText({ children, dir, className }: { children: string; dir?: string; className?: string }) {
  return (
    <div dir={dir} className={className}>
      <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
        {children}
      </ReactMarkdown>
    </div>
  )
}

// Flashcard Component
function FlashcardView({
  flashcards,
  onSeek,
  dir,
}: {
  flashcards: Flashcard[]
  onSeek: (ts: number) => void
  dir?: string
}) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)

  const card = flashcards[currentIndex]

  const goNext = () => {
    setIsFlipped(false)
    setTimeout(() => setCurrentIndex((i) => Math.min(i + 1, flashcards.length - 1)), 150)
  }

  const goPrev = () => {
    setIsFlipped(false)
    setTimeout(() => setCurrentIndex((i) => Math.max(i - 1, 0)), 150)
  }

  if (!card) return null

  return (
    <div className="h-full flex flex-col gap-4">
      <div
        className="perspective-1000 flex-1 min-h-0 cursor-pointer"
        onClick={() => setIsFlipped(!isFlipped)}
      >
        <div
          className={`relative w-full h-full preserve-3d transition-transform duration-500 ${
            isFlipped ? 'rotate-y-180' : ''
          }`}
        >
          {/* Front */}
          <div className="absolute inset-0 backface-hidden bg-surface border border-border rounded-lg p-6 flex items-center justify-center">
            <MarkdownText dir={dir} className="text-lg font-semibold text-text text-center prose prose-sm max-w-none">{card.question}</MarkdownText>
          </div>

          {/* Back */}
          <div className="absolute inset-0 backface-hidden rotate-y-180 bg-surface border border-border rounded-lg p-6 flex flex-col items-center justify-center overflow-auto">
            <MarkdownText dir={dir} className="text-text text-center prose prose-sm max-w-none">{card.answer}</MarkdownText>
            {card.citations[0] && (
              <div
                className="mt-3 p-3 bg-surface-alt rounded font-mono text-sm cursor-pointer hover:bg-muted transition-colors flex-shrink-0"
                onClick={(e) => {
                  e.stopPropagation()
                  onSeek(card.citations[0].start_ts)
                }}
              >
                <span className="text-accent font-medium">
                  {formatTimestamp(card.citations[0].start_ts)}
                </span>
                <span className="text-text-muted ml-2">&ldquo;{card.citations[0].quote}&rdquo;</span>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={goPrev}
          disabled={currentIndex === 0}
          className="p-2 rounded-lg hover:bg-surface disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-text" />
        </button>
        <span className="text-sm text-text-muted">
          {currentIndex + 1} of {flashcards.length}
        </span>
        <button
          onClick={goNext}
          disabled={currentIndex === flashcards.length - 1}
          className="p-2 rounded-lg hover:bg-surface disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronRight className="w-5 h-5 text-text" />
        </button>
      </div>
    </div>
  )
}

// Q&A Chat Component
function QAChat({
  videoId,
  onSeek,
  dir,
}: {
  videoId: string
  onSeek: (ts: number) => void
  dir?: string
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [toolUse, setToolUse] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)
    setToolUse(null)

    try {
      const response = await fetch(`${API}/api/qa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ video_id: videoId, question: userMessage }),
      })

      if (!response.ok) throw new Error('Failed to get response')

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let assistantMessage: ChatMessage = { 
        role: 'assistant', 
        content: '', 
        citations: [],
        isStreaming: true 
      }
      
      setMessages(prev => [...prev, assistantMessage])

      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event:')) {
            const eventType = line.slice(6).trim()
            
            if (eventType === 'tool-use') {
              setToolUse('Searching the web...')
            } else if (eventType === 'done') {
              setToolUse(null)
              assistantMessage.isStreaming = false
              setMessages(prev => [...prev.slice(0, -1), { ...assistantMessage }])
            }
          } else if (line.startsWith('data:')) {
            const data = line.slice(5).trim()
            try {
              const parsed = JSON.parse(data)
              
              if (parsed.text) {
                assistantMessage.content += parsed.text
                setMessages(prev => [...prev.slice(0, -1), { ...assistantMessage }])
              } else if (parsed.citation) {
                assistantMessage.citations = [
                  ...(assistantMessage.citations || []),
                  { timestamp: parsed.citation.start_ts, quote: parsed.citation.quote },
                ]
                setMessages(prev => [...prev.slice(0, -1), { ...assistantMessage }])
              }
            } catch {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch {
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }
      ])
    } finally {
      setIsLoading(false)
      setToolUse(null)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <p className="text-text-muted text-sm text-center py-8">
            Ask questions about the lecture...
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-4 py-2 ${
                msg.role === 'user'
                  ? 'bg-accent text-white'
                  : 'bg-surface text-text'
              }`}
            >
              {msg.role === 'assistant' ? (
                <MarkdownText dir={dir} className="text-sm prose prose-sm max-w-none">{msg.content}</MarkdownText>
              ) : (
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              )}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-2 space-y-1">
                  {msg.citations.map((citation, j) => (
                    <button
                      key={j}
                      onClick={() => onSeek(citation.timestamp)}
                      className="block w-full text-left font-mono text-xs bg-surface-alt rounded px-2 py-1 hover:bg-muted transition-colors"
                    >
                      <span className="text-accent font-medium">
                        {formatTimestamp(citation.timestamp)}
                      </span>
                      <span className="text-text-muted ml-1">&ldquo;{citation.quote}&rdquo;</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {toolUse && (
          <div className="flex justify-start">
            <span className="inline-flex items-center gap-2 bg-accent-light text-accent text-sm px-3 py-1.5 rounded-lg animate-pulse">
              <Loader2 className="w-4 h-4 animate-spin" />
              {toolUse}
            </span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => {
            setInput(e.target.value)
            const el = e.target
            el.style.height = 'auto'
            el.style.height = `${el.scrollHeight}px`
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSubmit(e as unknown as React.FormEvent)
            }
          }}
          placeholder="Ask a question..."
          className="flex-1 px-3 py-2 rounded-lg bg-surface border border-border text-text text-sm placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring resize-none overflow-hidden max-h-40"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="p-2 rounded-lg bg-accent text-white hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-shrink-0"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  )
}

// Main Study View Component
function StudyViewContent() {
  const searchParams = useSearchParams()
  const videoId = searchParams.get('id')
  const jobId = searchParams.get('job')

  const [studyPack, setStudyPack] = useState<StudyPack | null>(null)
  const [processing, setProcessing] = useState<ProcessingState>({
    metadata: false,
    transcript: false,
    outline: false,
    studyPack: false,
  })
  const [isProcessing, setIsProcessing] = useState(!!jobId)
  const [error, setError] = useState<ErrorState | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [leftWidth, setLeftWidth] = useState(240)
  const [rightWidth, setRightWidth] = useState(320)
  const [summaryDepth, setSummaryDepth] = useState<SummaryDepth>('five_minutes')
  const [rightTab, setRightTab] = useState<'flashcards' | 'qa'>('flashcards')
  const [selectedLanguage, setSelectedLanguage] = useState('en')
  const [isTranslating, setIsTranslating] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  const playerRef = useRef<HTMLIFrameElement>(null)
  const originalStudyPackRef = useRef<StudyPack | null>(null)
  const dragRef = useRef<{ side: 'left' | 'right'; startX: number; startWidth: number } | null>(null)

  const startDrag = (side: 'left' | 'right') => (e: React.PointerEvent) => {
    e.preventDefault()
    dragRef.current = {
      side,
      startX: e.clientX,
      startWidth: side === 'left' ? leftWidth : rightWidth,
    }
    const onMove = (ev: PointerEvent) => {
      if (!dragRef.current) return
      const delta = ev.clientX - dragRef.current.startX
      if (dragRef.current.side === 'left') {
        setLeftWidth(Math.max(160, Math.min(480, dragRef.current.startWidth + delta)))
      } else {
        setRightWidth(Math.max(240, Math.min(560, dragRef.current.startWidth - delta)))
      }
    }
    const onUp = () => {
      dragRef.current = null
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
  }

  const showToast = (message: string) => {
    setToast(message)
    setTimeout(() => setToast(null), 5000)
  }

  // Seek the YouTube player
  const seekTo = useCallback((timestamp: number) => {
    if (playerRef.current?.contentWindow) {
      playerRef.current.contentWindow.postMessage(
        JSON.stringify({
          event: 'command',
          func: 'seekTo',
          args: [timestamp, true],
        }),
        '*'
      )
    }
  }, [])

  // Handle SSE for processing
  useEffect(() => {
    if (!jobId) return

    const eventSource = new EventSource(`${API}/sse/video/${jobId}`, {
      withCredentials: true,
    })

    eventSource.addEventListener('metadata-gate-pass', () => {
      setProcessing(prev => ({ ...prev, metadata: true }))
    })

    eventSource.addEventListener('transcript-source', (e) => {
      const data = JSON.parse(e.data)
      setProcessing(prev => ({ ...prev, transcriptSource: data.source }))
    })

    eventSource.addEventListener('transcript-fetched', () => {
      setProcessing(prev => ({ ...prev, transcript: true }))
    })

    eventSource.addEventListener('outline-done', () => {
      setProcessing(prev => ({ ...prev, outline: true }))
    })

    eventSource.addEventListener('study-pack-done', (e) => {
      const data = JSON.parse(e.data)
      setProcessing(prev => ({ ...prev, studyPack: true }))
      originalStudyPackRef.current = data.study_pack
      setStudyPack(data.study_pack)
      setIsProcessing(false)
    })

    eventSource.addEventListener('error', (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data)
        setError({ code: data.code, detail: data.detail })
      } catch {
        setError({ code: 'unknown', detail: 'An unexpected error occurred.' })
      }
      setIsProcessing(false)
      eventSource.close()
    })

    eventSource.addEventListener('done', () => {
      eventSource.close()
    })

    return () => eventSource.close()
  }, [jobId])

  // Load study pack if no job (cache hit)
  useEffect(() => {
    if (jobId || !videoId || studyPack) return

    fetch(`${API}/api/video/${videoId}`, { credentials: 'include' })
      .then(async res => {
        const data = await res.json()
        if (!res.ok) {
          setError({ code: data.code ?? 'fetch_error', detail: data.detail ?? 'Failed to load study pack.' })
        } else {
          originalStudyPackRef.current = data.study_pack
          setStudyPack(data.study_pack)
        }
      })
      .catch(() => setError({ code: 'fetch_error', detail: 'Failed to load study pack.' }))
  }, [videoId, jobId, studyPack])

  // Handle language change
  const handleLanguageChange = async (lang: string) => {
    if (!videoId || !studyPack) return

    setSelectedLanguage(lang)

    if (lang === 'en') {
      if (originalStudyPackRef.current) {
        setStudyPack(originalStudyPackRef.current)
      }
      return
    }

    if (!originalStudyPackRef.current) {
      originalStudyPackRef.current = studyPack
    }

    setIsTranslating(true)

    try {
      const response = await fetch(`${API}/api/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ video_id: videoId, target_language: lang }),
      })

      if (response.status === 429) {
        const data = await response.json()
        showToast(`Translation limit reached. Try again in ${Math.ceil(data.retry_after_seconds / 60)} minutes.`)
        setSelectedLanguage('en')
        if (originalStudyPackRef.current) setStudyPack(originalStudyPackRef.current)
      } else if (response.ok) {
        const data = await response.json()
        setStudyPack(prev => prev ? {
          ...prev,
          summaries: data.summaries,
          flashcards: data.flashcards,
        } : null)
      }
    } catch {
      setSelectedLanguage('en')
      if (originalStudyPackRef.current) setStudyPack(originalStudyPackRef.current)
    } finally {
      setIsTranslating(false)
    }
  }

  // Error state
  if (error) {
    return <ErrorCard error={error} onRetry={() => window.location.reload()} />
  }

  // Processing state
  if (isProcessing) {
    return <ProcessingChecklist state={processing} />
  }

  // Loading state
  if (!studyPack) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
      </div>
    )
  }

  const isRtl = selectedLanguage === 'ar'

  const languages = [
    { code: 'en', label: 'English' },
    { code: 'es', label: 'Espanol' },
    { code: 'fr', label: 'Francais' },
    { code: 'zh', label: '中文' },
    { code: 'ar', label: 'العربية' },
    { code: 'pt', label: 'Portugues' },
  ]

  return (
    <div className="h-screen bg-background flex flex-col overflow-hidden">
      {toast && (
        <div className="fixed bottom-4 right-4 z-50 bg-surface border border-border rounded-lg px-4 py-3 shadow-lg text-text text-sm max-w-sm">
          {toast}
        </div>
      )}
      {/* Header */}
      <header className="sticky top-0 z-50 bg-surface border-b border-border px-4 py-3 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold text-text hover:text-accent transition-colors">Distill</Link>
        <h1 className="text-sm font-medium text-text-muted truncate max-w-md hidden sm:block font-mono">
          {studyPack.video_id}
        </h1>
        <div className="relative">
          {isTranslating && (
            <Loader2 className="w-4 h-4 text-accent animate-spin absolute right-8 top-1/2 -translate-y-1/2" />
          )}
          <select
            value={selectedLanguage}
            onChange={(e) => handleLanguageChange(e.target.value)}
            disabled={isTranslating}
            className="px-3 py-1.5 rounded-lg bg-surface-alt border border-border text-text text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
          >
            {languages.map(lang => (
              <option key={lang.code} value={lang.code}>{lang.label}</option>
            ))}
          </select>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar - Outline */}
        {sidebarOpen && (
          <aside
            style={{ width: leftWidth }}
            className="border-r border-border bg-background overflow-hidden flex-shrink-0 flex"
          >
            <div className="flex-1 overflow-auto p-4 min-w-0">
              <h2 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-4">
                Outline
              </h2>
              <OutlineTree nodes={studyPack.outline.nodes} onSeek={seekTo} />
            </div>
            <div
              onPointerDown={startDrag('left')}
              className="w-1 cursor-col-resize hover:bg-accent/40 active:bg-accent/60 transition-colors flex-shrink-0"
            />
          </aside>
        )}

        {/* Center - Video + Summary */}
        <main className="flex-1 overflow-auto px-6 py-4 min-w-0">
          {/* Sidebar toggle */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="mb-4 p-2 rounded-lg hover:bg-surface transition-colors inline-flex items-center gap-1 text-text-muted text-sm"
          >
            {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            {sidebarOpen ? 'Hide outline' : 'Show outline'}
          </button>

          {/* YouTube embed */}
          <div className="aspect-video w-full rounded-lg overflow-hidden border border-border mb-6">
            <iframe
              ref={playerRef}
              src={`https://www.youtube.com/embed/${videoId}?enablejsapi=1`}
              className="w-full h-full"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>

          {/* Summary depth toggle */}
          <div className="flex items-center gap-2 mb-4">
            {([
              { key: 'ninety_seconds' as SummaryDepth, label: '90 sec' },
              { key: 'five_minutes' as SummaryDepth, label: '5 min' },
              { key: 'full' as SummaryDepth, label: 'Full' },
            ]).map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setSummaryDepth(key)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  summaryDepth === key
                    ? 'bg-accent text-white'
                    : 'bg-surface text-text hover:bg-surface-alt'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Summary content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={summaryDepth}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="prose prose-sm max-w-none text-text"
            >
              <MarkdownText dir={isRtl ? 'rtl' : undefined}>
                {studyPack.summaries.find(s => s.depth === summaryDepth)?.text ?? ''}
              </MarkdownText>
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Right resize handle */}
        <div
          onPointerDown={startDrag('right')}
          className="w-1 flex-shrink-0 cursor-col-resize hover:bg-accent/40 active:bg-accent/60 transition-colors border-l border-border"
        />

        {/* Right sidebar - Flashcards & Q&A */}
        <aside
          style={{ width: rightWidth }}
          className="bg-background flex-shrink-0 flex flex-col overflow-hidden"
        >
          {/* Tab header */}
          <div className="flex border-b border-border">
            {(['flashcards', 'qa'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setRightTab(tab)}
                className={`flex-1 px-4 py-3 text-sm font-medium transition-colors relative ${
                  rightTab === tab ? 'text-accent' : 'text-text-muted hover:text-text'
                }`}
              >
                {tab === 'flashcards' ? 'Flashcards' : 'Q&A'}
                {rightTab === tab && (
                  <motion.div
                    layoutId="tab-underline"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent"
                  />
                )}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-hidden p-4 flex flex-col">
            {rightTab === 'flashcards' ? (
              <FlashcardView flashcards={studyPack.flashcards} onSeek={seekTo} dir={isRtl ? 'rtl' : undefined} />
            ) : (
              <QAChat videoId={videoId!} onSeek={seekTo} dir={isRtl ? 'rtl' : undefined} />
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}

// Wrap with Suspense for useSearchParams
export default function StudyViewPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
      </div>
    }>
      <StudyViewContent />
    </Suspense>
  )
}

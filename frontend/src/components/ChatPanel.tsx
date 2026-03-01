import { useState, useRef, useEffect } from 'react'
import type { CloudProvider } from '../App'
import type { ProviderModels } from './ProviderPanel'

export type ChatMode = '1' | '2' | '3' | 'ai_council'

export type ChatProvider = 'local' | CloudProvider

const CHAT_PROVIDER_OPTIONS: { id: ChatProvider; label: string }[] = [
  { id: 'local', label: 'Local (Ollama)' },
  { id: 'gemini', label: 'Gemini' },
  { id: 'grok', label: 'Grok' },
  { id: 'openai', label: 'OpenAI' },
]

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  speaker?: string // for multi-model: 'Gemini' | 'Grok' | 'OpenAI'
}

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

interface Props {
  models: ProviderModels
  chatMode: ChatMode
  onChatModeChange: (m: ChatMode) => void
}

export function ChatPanel({
  models,
  chatMode,
  onChatModeChange,
}: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const listRef = useRef<HTMLDivElement>(null)

  // Per-character agent statements and provider selection (1/2/3 char modes)
  const [char1Statement, setChar1Statement] = useState('')
  const [char1Provider, setChar1Provider] = useState<ChatProvider>('local')
  const [char2Statement, setChar2Statement] = useState('')
  const [char2Provider, setChar2Provider] = useState<ChatProvider>('gemini')
  const [char3Statement, setChar3Statement] = useState('')
  const [char3Provider, setChar3Provider] = useState<ChatProvider>('grok')

  useEffect(() => {
    listRef.current?.scrollTo(0, listRef.current.scrollHeight)
  }, [messages])

  const getCharProviders = (): ChatProvider[] => {
    if (chatMode === '1') return [char1Provider]
    if (chatMode === '2') return [char1Provider, char2Provider]
    return [char1Provider, char2Provider, char3Provider]
  }

  const getCharStatements = (): string[] => {
    if (chatMode === '1') return [char1Statement]
    if (chatMode === '2') return [char1Statement, char2Statement]
    return [char1Statement, char2Statement, char3Statement]
  }

  const handleSend = async () => {
    const text = input.trim()
    if (!text || loading) return

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
    }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const body: Record<string, unknown> = {
        messages: [...messages, userMsg].map((m) => ({ role: m.role, content: m.content })),
        ollama_model: models.ollama,
        gemini_model: models.gemini,
        grok_model: models.grok,
        openai_model: models.openai,
      }

      if (chatMode === '1') {
        body.mode = 'single'
        const p = getCharProviders()[0]
        body.provider = p === 'local' ? 'local' : 'cloud'
        body.cloud_provider = p !== 'local' ? p : null
        body.agent_statements = getCharStatements()
        body.character_providers = [p]
      } else if (chatMode === '2') {
        body.mode = 'dual'
        const ps = getCharProviders().slice(0, 2)
        body.agent_statements = getCharStatements().slice(0, 2)
        body.character_providers = ps
      } else if (chatMode === '3') {
        body.mode = 'triple'
        body.agent_statements = getCharStatements()
        body.character_providers = getCharProviders()
      } else {
        body.mode = 'ai_council'
      }

      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        const msg = err.detail || err.error || res.statusText || 'Chat failed'
        throw new Error(`Chat API ${res.status}: ${msg}. Ensure backend is running on port 8000.`)
      }

      const data = await res.json()

      if (data.replies && Array.isArray(data.replies)) {
        const newMsgs: ChatMessage[] = data.replies.map(
          (r: { speaker: string; content: string }) => ({
            id: crypto.randomUUID(),
            role: 'assistant' as const,
            content: r.content,
            speaker: r.speaker,
          })
        )
        setMessages((m) => [...m, ...newMsgs])
      } else if (data.content) {
        setMessages((m) => [
          ...m,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: data.content,
            speaker: data.speaker,
          },
        ])
      } else {
        throw new Error('Invalid response')
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chat failed')
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `Error: ${e instanceof Error ? e.message : 'Chat failed'}`,
          speaker: undefined,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const renderCharConfig = (label: string, statement: string, onStatement: (v: string) => void, prov: ChatProvider, onProv: (p: ChatProvider) => void) => (
    <div key={label} className="chat-char-config">
      <div className="chat-char-header">{label}</div>
      <div className="model-select-row">
        <span className="model-label">Provider</span>
        <select value={prov} onChange={(e) => onProv(e.target.value as ChatProvider)}>
          {CHAT_PROVIDER_OPTIONS.map((o) => (
            <option key={o.id} value={o.id}>{o.label}</option>
          ))}
        </select>
      </div>
      <div className="chat-agent-statement">
        <label>Agent / profile statement</label>
        <textarea
          value={statement}
          onChange={(e) => onStatement(e.target.value)}
          placeholder="Describe this character's role and personality…"
          rows={2}
        />
      </div>
    </div>
  )

  return (
    <div className="chat-panel">
      <h2>Chat</h2>

      <div className="chat-mode-row">
        <span className="chat-mode-label">Chat with:</span>
        <div className="chat-mode-options">
          {(['1', '2', '3', 'ai_council'] as const).map((m) => (
            <label key={m} className={`chat-mode-option ${chatMode === m ? 'selected' : ''}`}>
              <input
                type="radio"
                name="chatMode"
                value={m}
                checked={chatMode === m}
                onChange={() => onChatModeChange(m)}
              />
              <span>
                {m === '1' && '1 Character'}
                {m === '2' && '2 Characters'}
                {m === '3' && '3 Characters'}
                {m === 'ai_council' && 'AI Council'}
              </span>
            </label>
          ))}
        </div>
      </div>

      {chatMode === '1' && (
        <div className="chat-char-configs">
          {renderCharConfig('Character 1', char1Statement, setChar1Statement, char1Provider, setChar1Provider)}
        </div>
      )}

      {chatMode === '2' && (
        <div className="chat-char-configs">
          {renderCharConfig('Character 1', char1Statement, setChar1Statement, char1Provider, setChar1Provider)}
          {renderCharConfig('Character 2', char2Statement, setChar2Statement, char2Provider, setChar2Provider)}
        </div>
      )}

      {chatMode === '3' && (
        <div className="chat-char-configs">
          {renderCharConfig('Character 1', char1Statement, setChar1Statement, char1Provider, setChar1Provider)}
          {renderCharConfig('Character 2', char2Statement, setChar2Statement, char2Provider, setChar2Provider)}
          {renderCharConfig('Character 3', char3Statement, setChar3Statement, char3Provider, setChar3Provider)}
        </div>
      )}

      {chatMode === 'ai_council' && (
        <p className="chat-hint">
          AI Council: Gemini, Grok, OpenAI — each with hard-coded council personality.
        </p>
      )}

      <div className="chat-messages" ref={listRef}>
        {messages.length === 0 && (
          <p className="chat-empty">Start a conversation. No voice — text chat only.</p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`chat-msg chat-msg-${m.role}`}>
            {m.role === 'user' ? (
              <span className="chat-msg-label">You</span>
            ) : (
              <span className="chat-msg-label">{m.speaker || 'Assistant'}</span>
            )}
            <div className="chat-msg-content">{m.content}</div>
          </div>
        ))}
        {loading && (
          <div className="chat-msg chat-msg-assistant">
            <span className="chat-msg-label">…</span>
            <div className="chat-msg-content">Thinking…</div>
          </div>
        )}
      </div>

      {error && <div className="chat-error">{error}</div>}

      <div className="chat-input-row">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder="Type a message…"
          rows={2}
          disabled={loading}
        />
        <button
          className="btn btn-primary chat-send"
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  )
}

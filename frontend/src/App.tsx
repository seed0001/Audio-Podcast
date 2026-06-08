import { useState, useEffect } from 'react'
import { ProviderPanel, DEFAULT_MODELS, type ProviderModels, type LocalLLMConfig } from './components/ProviderPanel'
import { SourcesPanel } from './components/SourcesPanel'
import { FormatPanel } from './components/FormatPanel'
import { VoicesPanel } from './components/VoicesPanel'
import { PreviewPanel } from './components/PreviewPanel'
import { ChatPanel, type ChatMode } from './components/ChatPanel'
import { SettingsPanel } from './components/SettingsPanel'
import { TTSSetupPanel } from './components/TTSSetupPanel'
import './App.css'

export interface Source {
  id: string
  filename: string
}

export interface Voice {
  id: string
  name: string
  character_statement: string
  provider?: string
  type?: 'builtin' | 'custom'
}

export type FormatType = 'deep_dive' | 'brief' | 'critique' | 'debate' | 'ai_council_review'

export type CloudProvider = 'gemini' | 'grok' | 'openai'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

async function api<T>(path: string, opts?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {}
  if (opts?.body && typeof opts.body === 'string') headers['Content-Type'] = 'application/json'
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers: { ...headers, ...(opts?.headers as Record<string, string>) },
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || res.statusText)
  }
  return res.json()
}

export function useVoices() {
  const [voices, setVoices] = useState<Voice[]>([])
  const [loading, setLoading] = useState(true)

  const refetch = () => {
    setLoading(true)
    api<{ voices: Voice[] }>('/voices')
      .then((d) => setVoices(d.voices))
      .catch(() => setVoices([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    refetch()
  }, [])
  return { voices, loading, refetch }
}

export function useGenerate(
  sources: Source[],
  format: FormatType,
  provider: 'local' | 'cloud',
  cloudProvider: CloudProvider | null,
  models: ProviderModels,
  localLLM: LocalLLMConfig,
  host1Voice: string,
  host2Voice: string | null,
  host3Voice: string | null,
  host1Character: string,
  host2Character: string,
  host3Character: string,
  customPrompt: string | null
) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [result, setResult] = useState<unknown>(null)
  const [error, setError] = useState<string | null>(null)

  const generate = async () => {
    if (sources.length === 0) {
      setError('Add at least one source')
      return
    }
    setStatus('loading')
    setError(null)
    try {
      const r = await api('/generate', {
        method: 'POST',
        body: JSON.stringify({
          source_ids: sources.map((s) => s.id),
          format,
          provider: provider,
          cloud_provider: provider === 'cloud' ? cloudProvider : null,
          local_llm_host: provider === 'local' ? localLLM.host || undefined : undefined,
          local_llm_type: provider === 'local' ? localLLM.type || undefined : undefined,
          ollama_model: provider === 'local' ? localLLM.model || undefined : models.ollama,
          gemini_model: models.gemini,
          grok_model: models.grok,
          openai_model: models.openai,
          host1_voice_id: host1Voice,
          host2_voice_id: format !== 'brief' ? host2Voice || host1Voice : null,
          host3_voice_id: format === 'ai_council_review' ? host3Voice || host2Voice || host1Voice : null,
          host1_character: host1Character || undefined,
          host2_character: host2Character || undefined,
          host3_character: host3Character || undefined,
          custom_prompt: customPrompt || undefined,
        }),
      })
      setResult(r)
      setStatus('done')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generation failed')
      setStatus('error')
    }
  }

  return { generate, status, result, error }
}

function App() {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [ttsSetupOpen, setTtsSetupOpen] = useState(false)
  const [sources, setSources] = useState<Source[]>([])
  const [provider, setProvider] = useState<'local' | 'cloud'>('local')
  const [cloudProvider, setCloudProvider] = useState<CloudProvider>('gemini')
  const [format, setFormat] = useState<FormatType>('deep_dive')
  const [host1Voice, setHost1Voice] = useState('')
  const [host2Voice, setHost2Voice] = useState('')
  const [host3Voice, setHost3Voice] = useState('')
  const [host1Character, setHost1Character] = useState('')
  const [host2Character, setHost2Character] = useState('')
  const [host3Character, setHost3Character] = useState('')
  const [customPrompt, setCustomPrompt] = useState('')
  const [chatMode, setChatMode] = useState<ChatMode>('1')
  const [models, setModels] = useState<ProviderModels>(() => ({ ...DEFAULT_MODELS }))
  const [localLLM, setLocalLLM] = useState<LocalLLMConfig>({
    host: '', type: 'ollama', model: '', name: '',
  })

  const { voices, loading, refetch: refetchVoices } = useVoices()
  const { generate, status, result, error } = useGenerate(
    sources,
    format,
    provider,
    provider === 'cloud' ? cloudProvider : null,
    models,
    localLLM,
    host1Voice,
    format !== 'brief' ? host2Voice : '',
    format === 'ai_council_review' ? host3Voice : '',
    host1Character,
    host2Character,
    host3Character,
    customPrompt || null
  )

  useEffect(() => {
    if (voices.length > 0 && !host1Voice) setHost1Voice(voices[0].id)
    if (voices.length > 1 && !host2Voice) setHost2Voice(voices[1]?.id ?? voices[0].id)
    if (voices.length > 2 && !host3Voice) setHost3Voice(voices[2]?.id ?? voices[1]?.id ?? voices[0].id)
    if (voices.length === 0) {
      setHost1Voice('')
      setHost2Voice('')
      setHost3Voice('')
    }
  }, [voices, host1Voice, host2Voice, host3Voice])

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <h1>Audio Overview Studio</h1>
          <p>Podcast-style summaries from your documents. Custom voices.</p>
        </div>
        <div className="header-actions">
          <button
            className="btn btn-primary tts-setup-btn"
            onClick={() => setTtsSetupOpen(true)}
            title="Configure TTS providers"
          >
            🎙 TTS Setup
          </button>
          <button
            className="btn btn-outline settings-open-btn"
            onClick={() => setSettingsOpen(true)}
            title="Prompt Settings"
          >
            ⚙ Prompts
          </button>
        </div>
      </header>

      {settingsOpen && (
        <SettingsPanel apiBase={API_BASE} onClose={() => setSettingsOpen(false)} />
      )}

      {ttsSetupOpen && (
        <TTSSetupPanel
          apiBase={API_BASE}
          onClose={() => setTtsSetupOpen(false)}
          onProviderChanged={refetchVoices}
        />
      )}

      <main className="main">
        <section className="panel provider-panel">
          <ProviderPanel
            provider={provider}
            cloudProvider={cloudProvider}
            models={models}
            localLLM={localLLM}
            onProviderChange={setProvider}
            onCloudProviderChange={setCloudProvider}
            onModelsChange={setModels}
            onLocalLLMChange={setLocalLLM}
          />
        </section>
        <section className="panel sources-panel">
          <SourcesPanel sources={sources} onSourcesChange={setSources} apiBase={API_BASE} />
        </section>

        <section className="panel format-panel">
          <FormatPanel
            format={format}
            onFormatChange={setFormat}
            customPrompt={customPrompt}
            onCustomPromptChange={setCustomPrompt}
          />
        </section>

        <section className="panel voices-panel">
          <VoicesPanel
            voices={voices}
            loading={loading}
            format={format}
            host1Voice={host1Voice}
            host2Voice={host2Voice}
            host3Voice={host3Voice}
            host1Character={host1Character}
            host2Character={host2Character}
            host3Character={host3Character}
            onHost1Change={setHost1Voice}
            onHost2Change={setHost2Voice}
            onHost3Change={setHost3Voice}
            onHost1CharacterChange={setHost1Character}
            onHost2CharacterChange={setHost2Character}
            onHost3CharacterChange={setHost3Character}
            onVoiceUploaded={refetchVoices}
            apiBase={API_BASE}
          />
        </section>

        <section className="panel preview-panel">
          <PreviewPanel
            onGenerate={generate}
            status={status}
            result={result}
            error={error}
          />
        </section>

        <section className="panel chat-panel-wrapper">
          <ChatPanel
            models={models}
            chatMode={chatMode}
            onChatModeChange={setChatMode}
          />
        </section>
      </main>
    </div>
  )
}

export default App

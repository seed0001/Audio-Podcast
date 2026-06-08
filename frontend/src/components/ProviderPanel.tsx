import { useState, useEffect, useCallback } from 'react'
import type { CloudProvider } from '../App'

const API_BASE = '/api'

export interface ProviderModels {
  ollama: string
  gemini: string
  grok: string
  openai: string
}

export const DEFAULT_MODELS: ProviderModels = {
  ollama: '',
  gemini: 'gemini-2.5-flash',
  grok: 'grok-3',
  openai: 'gpt-4o',
}

export interface LocalLLMConfig {
  host: string
  type: 'ollama' | 'openai_compat'
  model: string
  name: string
}

interface DetectedServer {
  name: string
  host: string
  type: 'ollama' | 'openai_compat'
  models: string[]
}

const GEMINI_MODELS = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-1.5-flash', 'gemini-1.5-pro']
const GROK_MODELS = ['grok-3', 'grok-2', 'grok-beta']
const OPENAI_MODELS = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo']

interface Props {
  provider: 'local' | 'cloud'
  cloudProvider: CloudProvider
  models: ProviderModels
  localLLM: LocalLLMConfig
  onProviderChange: (p: 'local' | 'cloud') => void
  onCloudProviderChange: (p: CloudProvider) => void
  onModelsChange: (m: ProviderModels) => void
  onLocalLLMChange: (cfg: LocalLLMConfig) => void
}

const CLOUD_OPTIONS: { id: CloudProvider; label: string }[] = [
  { id: 'gemini', label: 'Gemini (Google)' },
  { id: 'grok', label: 'Grok (xAI)' },
  { id: 'openai', label: 'OpenAI (GPT)' },
]

export function ProviderPanel({
  provider,
  cloudProvider,
  models,
  localLLM,
  onProviderChange,
  onCloudProviderChange,
  onModelsChange,
  onLocalLLMChange,
}: Props) {
  const [servers, setServers] = useState<DetectedServer[]>([])
  const [scanning, setScanning] = useState(false)
  const [scanDone, setScanDone] = useState(false)
  const [customHost, setCustomHost] = useState('')
  const [probing, setProbing] = useState(false)
  const [probeError, setProbeError] = useState<string | null>(null)

  const scan = useCallback(async () => {
    setScanning(true)
    setScanDone(false)
    try {
      const r = await fetch(`${API_BASE}/local-llms`)
      const d = await r.json()
      const found: DetectedServer[] = d.servers || []
      setServers(found)

      // Auto-select first server if nothing is selected yet or previous selection is gone
      if (found.length > 0) {
        const stillValid = found.some((s) => s.host === localLLM.host)
        if (!stillValid) {
          const first = found[0]
          onLocalLLMChange({
            host: first.host,
            type: first.type,
            model: first.models[0] || '',
            name: first.name,
          })
        }
      }
    } catch {
      setServers([])
    } finally {
      setScanning(false)
      setScanDone(true)
    }
  }, [localLLM.host, onLocalLLMChange])

  useEffect(() => {
    if (provider === 'local') scan()
  }, [provider]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSelectServer = (s: DetectedServer) => {
    onLocalLLMChange({
      host: s.host,
      type: s.type,
      model: s.models[0] || '',
      name: s.name,
    })
  }

  const handleProbeCustom = async () => {
    const host = customHost.trim()
    if (!host) return
    setProbing(true)
    setProbeError(null)
    try {
      const r = await fetch(`${API_BASE}/probe-llm?host=${encodeURIComponent(host)}`)
      const d = await r.json()
      if (d.available) {
        const server: DetectedServer = {
          name: d.name,
          host: d.host,
          type: d.type,
          models: d.models || [],
        }
        setServers((prev) => {
          const exists = prev.some((s) => s.host === server.host)
          return exists ? prev : [...prev, server]
        })
        onLocalLLMChange({
          host: server.host,
          type: server.type,
          model: server.models[0] || '',
          name: server.name,
        })
        setCustomHost('')
      } else {
        setProbeError(d.error || 'No LLM API found at that address.')
      }
    } catch {
      setProbeError('Could not connect.')
    } finally {
      setProbing(false)
    }
  }

  const selectedServer = servers.find((s) => s.host === localLLM.host)
  const modelOptions = selectedServer?.models || (localLLM.model ? [localLLM.model] : [])

  const setModel = (key: keyof ProviderModels, value: string) =>
    onModelsChange({ ...models, [key]: value })

  return (
    <div>
      <h2>Provider</h2>
      <div className="provider-toggle">
        <label className={`provider-option ${provider === 'local' ? 'selected' : ''}`}>
          <input type="radio" name="provider" value="local"
            checked={provider === 'local'} onChange={() => onProviderChange('local')} />
          <span>Local LLM</span>
        </label>
        <label className={`provider-option ${provider === 'cloud' ? 'selected' : ''}`}>
          <input type="radio" name="provider" value="cloud"
            checked={provider === 'cloud'} onChange={() => onProviderChange('cloud')} />
          <span>Cloud</span>
        </label>
      </div>

      {/* ── LOCAL ── */}
      {provider === 'local' && (
        <div className="local-llm-section">
          <div className="local-llm-header">
            <span className="local-llm-label">Detected local LLM servers</span>
            <button
              className="btn btn-outline local-llm-scan-btn"
              onClick={scan}
              disabled={scanning}
            >
              {scanning ? 'Scanning…' : '⟳ Scan'}
            </button>
          </div>

          {scanning && <p className="hint">Scanning common ports…</p>}

          {!scanning && scanDone && servers.length === 0 && (
            <div className="ollama-error">
              <strong>⚠ No local LLM servers found</strong>
              <p>
                Supported: <strong>Ollama</strong>, <strong>LM Studio</strong>, <strong>Jan</strong>,{' '}
                <strong>llama.cpp</strong>, <strong>GPT4All</strong>, and any OpenAI-compatible server.
              </p>
              <p>
                Start one of those apps, then click <strong>⟳ Scan</strong>. Or enter a custom address below.
                You can also switch to <strong>Cloud</strong> above.
              </p>
            </div>
          )}

          {servers.length > 0 && (
            <div className="local-server-list">
              {servers.map((s) => {
                const isSelected = localLLM.host === s.host
                return (
                  <button
                    key={s.host}
                    className={`local-server-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleSelectServer(s)}
                  >
                    <span className="local-server-name">
                      {isSelected ? '● ' : '○ '}{s.name}
                    </span>
                    <span className="local-server-host">{s.host}</span>
                    <span className="local-server-models">
                      {s.models.length > 0
                        ? `${s.models.length} model${s.models.length !== 1 ? 's' : ''}`
                        : 'no models listed'}
                    </span>
                  </button>
                )
              })}
            </div>
          )}

          {/* Model selector for selected server */}
          {localLLM.host && (
            <div className="model-select-row" style={{ marginTop: '0.75rem' }}>
              <label>Model</label>
              {modelOptions.length > 0 ? (
                <select
                  value={localLLM.model}
                  onChange={(e) => onLocalLLMChange({ ...localLLM, model: e.target.value })}
                >
                  {modelOptions.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  className="local-model-input"
                  placeholder="Enter model name (e.g. llama3.2)"
                  value={localLLM.model}
                  onChange={(e) => onLocalLLMChange({ ...localLLM, model: e.target.value })}
                />
              )}
            </div>
          )}

          {/* Custom host input */}
          <div className="local-custom-host">
            <label className="local-llm-label">Custom server address</label>
            <div className="local-custom-row">
              <input
                type="text"
                className="local-host-input"
                placeholder="http://localhost:8080"
                value={customHost}
                onChange={(e) => setCustomHost(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleProbeCustom()}
              />
              <button
                className="btn btn-outline"
                onClick={handleProbeCustom}
                disabled={probing || !customHost.trim()}
              >
                {probing ? '…' : 'Connect'}
              </button>
            </div>
            {probeError && <p className="upload-error">{probeError}</p>}
          </div>
        </div>
      )}

      {/* ── CLOUD ── */}
      {provider === 'cloud' && (
        <>
          <div className="cloud-provider-select">
            <label>Cloud provider</label>
            <select
              value={cloudProvider}
              onChange={(e) => onCloudProviderChange(e.target.value as CloudProvider)}
            >
              {CLOUD_OPTIONS.map((o) => (
                <option key={o.id} value={o.id}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="cloud-models-section">
            <label>Models (for audio, chat & AI Council)</label>
            <div className="model-select-row">
              <span className="model-label">Gemini</span>
              <select value={models.gemini} onChange={(e) => setModel('gemini', e.target.value)}>
                {GEMINI_MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div className="model-select-row">
              <span className="model-label">Grok</span>
              <select value={models.grok} onChange={(e) => setModel('grok', e.target.value)}>
                {GROK_MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div className="model-select-row">
              <span className="model-label">OpenAI</span>
              <select value={models.openai} onChange={(e) => setModel('openai', e.target.value)}>
                {OPENAI_MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

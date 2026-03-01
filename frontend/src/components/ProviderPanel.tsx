import { useState, useEffect } from 'react'
import type { CloudProvider } from '../App'

const API_BASE = '/api'

export interface ProviderModels {
  ollama: string
  gemini: string
  grok: string
  openai: string
}

export const DEFAULT_MODELS: ProviderModels = {
  ollama: 'llama3.2',
  gemini: 'gemini-2.5-flash',
  grok: 'grok-3',
  openai: 'gpt-4o',
}

const GEMINI_MODELS = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-1.5-flash', 'gemini-1.5-pro']
const GROK_MODELS = ['grok-3', 'grok-2', 'grok-beta']
const OPENAI_MODELS = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo']

interface Props {
  provider: 'local' | 'cloud'
  cloudProvider: CloudProvider
  models: ProviderModels
  onProviderChange: (p: 'local' | 'cloud') => void
  onCloudProviderChange: (p: CloudProvider) => void
  onModelsChange: (m: ProviderModels) => void
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
  onProviderChange,
  onCloudProviderChange,
  onModelsChange,
}: Props) {
  const [ollamaModels, setOllamaModels] = useState<string[]>([])
  const [ollamaLoading, setOllamaLoading] = useState(false)

  useEffect(() => {
    if (provider !== 'local') return
    setOllamaLoading(true)
    fetch(`${API_BASE}/ollama-models`)
      .then((r) => r.json())
      .then((d) => setOllamaModels(d.models || []))
      .catch(() => setOllamaModels([]))
      .finally(() => setOllamaLoading(false))
  }, [provider])

  const setModel = (key: keyof ProviderModels, value: string) => {
    onModelsChange({ ...models, [key]: value })
  }

  const ollamaOptions = ollamaModels.length > 0
    ? ollamaModels
    : models.ollama ? [models.ollama] : []

  return (
    <div>
      <h2>Provider</h2>
      <div className="provider-toggle">
        <label className={`provider-option ${provider === 'local' ? 'selected' : ''}`}>
          <input
            type="radio"
            name="provider"
            value="local"
            checked={provider === 'local'}
            onChange={() => onProviderChange('local')}
          />
          <span>Local (Ollama)</span>
        </label>
        <label className={`provider-option ${provider === 'cloud' ? 'selected' : ''}`}>
          <input
            type="radio"
            name="provider"
            value="cloud"
            checked={provider === 'cloud'}
            onChange={() => onProviderChange('cloud')}
          />
          <span>Cloud</span>
        </label>
      </div>

      {provider === 'local' && (
        <div className="model-select-row">
          <label>Ollama model</label>
          <select
            value={models.ollama}
            onChange={(e) => setModel('ollama', e.target.value)}
            disabled={ollamaLoading}
          >
            {ollamaOptions.length === 0 && (
              <option value="">{ollamaLoading ? 'Loading…' : 'No models (run ollama pull)'}</option>
            )}
            {ollamaOptions.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
      )}

      {provider === 'cloud' && (
        <>
          <div className="cloud-provider-select">
            <label>Cloud provider</label>
            <select
              value={cloudProvider}
              onChange={(e) => onCloudProviderChange(e.target.value as CloudProvider)}
            >
              {CLOUD_OPTIONS.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="cloud-models-section">
            <label>Models (for audio, chat & AI Council)</label>
            <div className="model-select-row">
              <span className="model-label">Gemini</span>
              <select value={models.gemini} onChange={(e) => setModel('gemini', e.target.value)}>
                {GEMINI_MODELS.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
            <div className="model-select-row">
              <span className="model-label">Grok</span>
              <select value={models.grok} onChange={(e) => setModel('grok', e.target.value)}>
                {GROK_MODELS.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
            <div className="model-select-row">
              <span className="model-label">OpenAI</span>
              <select value={models.openai} onChange={(e) => setModel('openai', e.target.value)}>
                {OPENAI_MODELS.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

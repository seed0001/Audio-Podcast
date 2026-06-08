import { useState, useEffect, useCallback } from 'react'

interface ProviderStatus {
  available: boolean
  reason: string | null
}

interface TTSConfig {
  active_provider: string
  openai_api_key_set: boolean
  openai_model: string
  elevenlabs_api_key_set: boolean
  elevenlabs_model: string
  luxtts_path: string
  providers: {
    openai: ProviderStatus
    elevenlabs: ProviderStatus
    kokoro: ProviderStatus
    luxtts: ProviderStatus
  }
}

interface Props {
  apiBase: string
  onClose: () => void
  onProviderChanged: () => void
}

const PROVIDER_META: Record<string, { label: string; description: string; learnMore?: string }> = {
  openai: {
    label: 'OpenAI TTS',
    description: 'High-quality cloud TTS. Six built-in voices. Uses your OpenAI API key.',
  },
  elevenlabs: {
    label: 'ElevenLabs',
    description: 'Best-in-class podcast voices. Free tier available (10k chars/month). API key required.',
    learnMore: 'https://elevenlabs.io',
  },
  kokoro: {
    label: 'Kokoro (Local)',
    description: 'Runs entirely on your machine — no API key, no internet needed. Install with pip.',
  },
  luxtts: {
    label: 'LuxTTS (Advanced)',
    description: 'Voice cloning from your own audio samples. Requires a separate repo install and GPU recommended.',
  },
}

const OPENAI_MODELS = ['tts-1', 'tts-1-hd']
const ELEVENLABS_MODELS = [
  { id: 'eleven_turbo_v2_5', label: 'Turbo v2.5 (fast, great quality)' },
  { id: 'eleven_multilingual_v2', label: 'Multilingual v2 (highest quality)' },
  { id: 'eleven_turbo_v2', label: 'Turbo v2' },
]

const TEST_VOICES: Record<string, string> = {
  openai: 'openai:nova',
  elevenlabs: 'elevenlabs:21m00Tcm4TlvDq8ikWAM',
  kokoro: 'kokoro:af_heart',
  luxtts: '',
}

export function TTSSetupPanel({ apiBase, onClose, onProviderChanged }: Props) {
  const [config, setConfig] = useState<TTSConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)

  // Editable fields
  const [activeProvider, setActiveProvider] = useState('')
  const [openaiKey, setOpenaiKey] = useState('')
  const [openaiModel, setOpenaiModel] = useState('tts-1-hd')
  const [elKey, setElKey] = useState('')
  const [elModel, setElModel] = useState('eleven_turbo_v2_5')
  const [luxttsPath, setLuxttsPath] = useState('')

  // Test audio
  const [testing, setTesting] = useState<string | null>(null)
  const [testAudio, setTestAudio] = useState<HTMLAudioElement | null>(null)
  const [testError, setTestError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${apiBase}/tts-config`)
      if (!res.ok) throw new Error(await res.text())
      const data: TTSConfig = await res.json()
      setConfig(data)
      setActiveProvider(data.active_provider)
      setOpenaiModel(data.openai_model || 'tts-1-hd')
      setElModel(data.elevenlabs_model || 'eleven_turbo_v2_5')
      setLuxttsPath(data.luxtts_path || '')
    } catch {
      // silently keep loading state
    } finally {
      setLoading(false)
    }
  }, [apiBase])

  useEffect(() => {
    load()
  }, [load])

  const handleSave = async () => {
    setSaving(true)
    setSaveMsg(null)
    try {
      const body: Record<string, string> = {
        active_provider: activeProvider,
        openai_model: openaiModel,
        elevenlabs_model: elModel,
        luxtts_path: luxttsPath,
      }
      if (openaiKey.trim()) body.openai_api_key = openaiKey.trim()
      if (elKey.trim()) body.elevenlabs_api_key = elKey.trim()

      const res = await fetch(`${apiBase}/tts-config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(await res.text())
      const data: TTSConfig = await res.json()
      setConfig(data)
      setOpenaiKey('')
      setElKey('')
      setSaveMsg('Saved.')
      onProviderChanged()
      setTimeout(() => setSaveMsg(null), 3000)
    } catch (e) {
      setSaveMsg(`Error: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async (provider: string) => {
    const voiceId = TEST_VOICES[provider]
    if (!voiceId) {
      setTestError('Upload a custom voice first to test LuxTTS.')
      return
    }
    if (testAudio) {
      testAudio.pause()
      setTestAudio(null)
    }
    setTesting(provider)
    setTestError(null)
    try {
      const res = await fetch(`${apiBase}/tts-test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice_id: voiceId }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(typeof err.detail === 'string' ? err.detail : 'Test failed')
      }
      const data = await res.json()
      const audio = new Audio(`${apiBase.replace('/api', '')}${data.audio_url}`)
      setTestAudio(audio)
      audio.play()
    } catch (e) {
      setTestError(e instanceof Error ? e.message : 'Test failed')
    } finally {
      setTesting(null)
    }
  }

  const statusDot = (p: ProviderStatus) =>
    p.available ? '🟢' : '🔴'

  const providers = ['openai', 'elevenlabs', 'kokoro', 'luxtts'] as const

  return (
    <div className="settings-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="settings-panel tts-setup-panel">
        <div className="settings-header">
          <div className="settings-header-left">
            <h2>TTS Setup</h2>
            <p className="settings-subtitle">
              Configure your text-to-speech engine. TTS is the core of every podcast — pick the provider that fits your setup.
            </p>
          </div>
          <button className="btn-icon settings-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="settings-top-actions">
          <button className="btn btn-primary" onClick={handleSave} disabled={saving || loading}>
            {saving ? 'Saving…' : 'Save & Apply'}
          </button>
          {saveMsg && (
            <span className={`settings-save-msg ${saveMsg.startsWith('Error') ? 'settings-save-error' : 'settings-save-ok'}`}>
              {saveMsg}
            </span>
          )}
        </div>

        {loading && <p className="settings-loading">Loading TTS config…</p>}

        {!loading && config && (
          <div className="settings-body">
            {/* Active provider selector */}
            <div className="tts-active-row">
              <label className="settings-label">Active Provider</label>
              <div className="tts-provider-selector">
                {providers.map((p) => (
                  <button
                    key={p}
                    className={`tts-provider-chip ${activeProvider === p ? 'active' : ''}`}
                    onClick={() => setActiveProvider(p)}
                  >
                    {statusDot(config.providers[p])} {PROVIDER_META[p].label}
                  </button>
                ))}
              </div>
            </div>

            {/* Provider cards */}
            {providers.map((p) => {
              const meta = PROVIDER_META[p]
              const status = config.providers[p]
              const isActive = activeProvider === p

              return (
                <div key={p} className={`tts-provider-card ${isActive ? 'tts-card-active' : ''}`}>
                  <div className="tts-card-header">
                    <div>
                      <span className="tts-card-title">
                        {statusDot(status)} {meta.label}
                        {isActive && <span className="tts-active-badge">ACTIVE</span>}
                      </span>
                      <p className="tts-card-desc">{meta.description}</p>
                    </div>
                    <button
                      className="btn btn-outline tts-test-btn"
                      onClick={() => handleTest(p)}
                      disabled={!status.available || testing === p}
                    >
                      {testing === p ? '…' : '▶ Test'}
                    </button>
                  </div>

                  {!status.available && status.reason && (
                    <div className="tts-card-notice">
                      {p === 'kokoro' ? (
                        <>
                          <strong>Not installed.</strong>
                          <p className="tts-install-cmd">
                            <strong>Windows:</strong> <code>pip install kokoro[en] misaki[en]</code>
                            <br />
                            <strong>Mac / Linux:</strong> <code>pip install kokoro[en]</code>
                          </p>
                          <p className="hint">Then restart the backend server.</p>
                        </>
                      ) : (
                        <span>{status.reason}</span>
                      )}
                    </div>
                  )}

                  {/* OpenAI config */}
                  {p === 'openai' && (
                    <div className="tts-card-config">
                      <label className="settings-label">
                        API Key {config.openai_api_key_set && <span className="tts-key-set">● set</span>}
                      </label>
                      <input
                        type="password"
                        className="tts-key-input"
                        placeholder={config.openai_api_key_set ? '••••••••  (leave blank to keep current)' : 'sk-…'}
                        value={openaiKey}
                        onChange={(e) => setOpenaiKey(e.target.value)}
                        autoComplete="off"
                      />
                      <label className="settings-label" style={{ marginTop: '0.5rem' }}>Model</label>
                      <select
                        className="tts-select"
                        value={openaiModel}
                        onChange={(e) => setOpenaiModel(e.target.value)}
                      >
                        {OPENAI_MODELS.map((m) => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                      <p className="hint">
                        <strong>tts-1-hd</strong> = highest quality (recommended for podcasts) &nbsp;|&nbsp; <strong>tts-1</strong> = faster, lower cost
                      </p>
                      <p className="hint">Voices: Alloy, Echo, Fable, Onyx, Nova, Shimmer — select in the Voices panel.</p>
                    </div>
                  )}

                  {/* ElevenLabs config */}
                  {p === 'elevenlabs' && (
                    <div className="tts-card-config">
                      <label className="settings-label">
                        API Key {config.elevenlabs_api_key_set && <span className="tts-key-set">● set</span>}
                      </label>
                      <input
                        type="password"
                        className="tts-key-input"
                        placeholder={config.elevenlabs_api_key_set ? '••••••••  (leave blank to keep current)' : 'Your ElevenLabs API key'}
                        value={elKey}
                        onChange={(e) => setElKey(e.target.value)}
                        autoComplete="off"
                      />
                      <label className="settings-label" style={{ marginTop: '0.5rem' }}>Model</label>
                      <select
                        className="tts-select"
                        value={elModel}
                        onChange={(e) => setElModel(e.target.value)}
                      >
                        {ELEVENLABS_MODELS.map((m) => (
                          <option key={m.id} value={m.id}>{m.label}</option>
                        ))}
                      </select>
                      <p className="hint">
                        Get your API key at <strong>elevenlabs.io</strong> → Profile → API Keys. Free tier: 10,000 chars/month.
                      </p>
                    </div>
                  )}

                  {/* Kokoro config */}
                  {p === 'kokoro' && status.available && (
                    <div className="tts-card-config">
                      <p className="hint">
                        Kokoro runs locally — no API key, no internet needed. 11 voices across US and British English accents.
                        First generation may take a moment while the model loads.
                      </p>
                    </div>
                  )}

                  {/* LuxTTS config */}
                  {p === 'luxtts' && (
                    <div className="tts-card-config">
                      <label className="settings-label">Path to temp_luxtts</label>
                      <input
                        type="text"
                        className="tts-key-input"
                        placeholder="/path/to/temp_luxtts  (or set AOS_LUXTTS_PATH in .env)"
                        value={luxttsPath}
                        onChange={(e) => setLuxttsPath(e.target.value)}
                      />
                      <p className="hint">
                        LuxTTS requires voice cloning from uploaded MP3 samples. Upload voices in the Voices panel.
                        Also install: <code>pip install torch torchaudio</code> then the requirements from the LuxTTS repo.
                      </p>
                    </div>
                  )}
                </div>
              )
            })}

            {testError && (
              <div className="tts-test-error">
                <strong>Test failed:</strong> {testError}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

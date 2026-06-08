import { useState, useRef } from 'react'
import type { Voice } from '../App'

interface Props {
  voices: Voice[]
  loading: boolean
  format: string
  host1Voice: string
  host2Voice: string
  host3Voice: string
  onHost1Change: (id: string) => void
  onHost2Change: (id: string) => void
  onHost3Change: (id: string) => void
  onVoiceUploaded: () => void
  apiBase: string
}

const PROVIDER_LABELS: Record<string, string> = {
  openai: 'OpenAI',
  elevenlabs: 'ElevenLabs',
  kokoro: 'Kokoro',
  luxtts: 'LuxTTS',
}

export function VoicesPanel({
  voices,
  loading,
  format,
  host1Voice,
  host2Voice,
  host3Voice,
  onHost1Change,
  onHost2Change,
  onHost3Change,
  onVoiceUploaded,
  apiBase,
}: Props) {
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [voiceName, setVoiceName] = useState('')
  const [characterStatement, setCharacterStatement] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const showHost2 = format !== 'brief'
  const showHost3 = format === 'ai_council_review'

  // Determine active provider from the first available voice
  const activeProvider = voices.length > 0 ? (voices[0].provider || 'luxtts') : null
  const showUpload = activeProvider === 'luxtts' || !activeProvider

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.mp3')) {
      setUploadError('Only MP3 files are supported.')
      return
    }
    if (!voiceName.trim()) {
      setUploadError('Name is required.')
      return
    }
    setUploading(true)
    setUploadError(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('name', voiceName.trim())
      fd.append('character_statement', characterStatement.trim())
      const res = await fetch(`${apiBase}/voices/upload`, {
        method: 'POST',
        body: fd,
      })
      if (!res.ok) {
        const err = await res.text()
        throw new Error(err || res.statusText)
      }
      const data = await res.json()
      const voiceId = `luxtts:${data.id}`
      onHost1Change(voiceId)
      if (showHost2) onHost2Change(voiceId)
      if (showHost3) onHost3Change(voiceId)
      onVoiceUploaded()
      setVoiceName('')
      setCharacterStatement('')
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const voiceLabel = (v: Voice) => {
    const providerTag = v.provider ? ` (${PROVIDER_LABELS[v.provider] ?? v.provider})` : ''
    return `${v.name}${providerTag}`
  }

  return (
    <div>
      <h2>Voices</h2>
      {loading ? (
        <p className="hint">Loading voices…</p>
      ) : (
        <>
          {voices.length === 0 ? (
            <div className="tts-no-voices">
              <p className="hint">No voices available.</p>
              <p className="hint">
                Open <strong>TTS Setup</strong> to configure a provider, then voices will appear here automatically.
                {showUpload && ' Or upload an MP3 below for LuxTTS voice cloning.'}
              </p>
            </div>
          ) : (
            <>
              <div className="voice-row">
                <label>Host 1</label>
                <select value={host1Voice} onChange={(e) => onHost1Change(e.target.value)}>
                  {voices.map((v) => (
                    <option key={v.id} value={v.id}>{voiceLabel(v)}</option>
                  ))}
                </select>
              </div>

              {showHost2 && (
                <div className="voice-row">
                  <label>Host 2</label>
                  <select value={host2Voice} onChange={(e) => onHost2Change(e.target.value)}>
                    {voices.map((v) => (
                      <option key={v.id} value={v.id}>{voiceLabel(v)}</option>
                    ))}
                  </select>
                </div>
              )}

              {showHost3 && (
                <div className="voice-row">
                  <label>Host 3 (Council)</label>
                  <select value={host3Voice} onChange={(e) => onHost3Change(e.target.value)}>
                    {voices.map((v) => (
                      <option key={v.id} value={v.id}>{voiceLabel(v)}</option>
                    ))}
                  </select>
                </div>
              )}
            </>
          )}

          {/* Voice upload — only shown when LuxTTS is active */}
          {showUpload && (
            <div className="voice-upload">
              <h3 className="voice-upload-title">Upload custom voice (LuxTTS)</h3>
              <input
                ref={fileInputRef}
                type="file"
                accept=".mp3,audio/mpeg"
                onChange={handleUpload}
                style={{ display: 'none' }}
              />
              <label>Name</label>
              <input
                type="text"
                placeholder="e.g. Morgan"
                value={voiceName}
                onChange={(e) => setVoiceName(e.target.value)}
                className="voice-name-input"
              />
              <label>Character statement</label>
              <textarea
                placeholder="How they speak. e.g. Calm, measured tone. Speaks slowly with deliberate pauses."
                value={characterStatement}
                onChange={(e) => setCharacterStatement(e.target.value)}
                className="voice-character-input"
                rows={3}
              />
              <button
                className="btn btn-outline"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                style={{ marginTop: '0.5rem' }}
              >
                {uploading ? 'Uploading…' : 'Select audio sample (MP3)'}
              </button>
              {uploadError && <p className="upload-error">{uploadError}</p>}
            </div>
          )}

          {!showUpload && voices.length > 0 && (
            <p className="hint" style={{ marginTop: '0.75rem' }}>
              Using <strong>{PROVIDER_LABELS[activeProvider!] ?? activeProvider}</strong> voices.
              Switch providers in <strong>TTS Setup</strong>.
            </p>
          )}
        </>
      )}
    </div>
  )
}

import { useState, useRef } from 'react'
import type { Voice } from '../App'

interface Props {
  voices: Voice[]
  loading: boolean
  format: string
  host1Voice: string
  host2Voice: string
  host3Voice: string
  host1Character: string
  host2Character: string
  host3Character: string
  onHost1Change: (id: string) => void
  onHost2Change: (id: string) => void
  onHost3Change: (id: string) => void
  onHost1CharacterChange: (s: string) => void
  onHost2CharacterChange: (s: string) => void
  onHost3CharacterChange: (s: string) => void
  onVoiceUploaded: () => void
  apiBase: string
}

const PROVIDER_LABELS: Record<string, string> = {
  openai: 'OpenAI',
  elevenlabs: 'ElevenLabs',
  kokoro: 'Kokoro',
  luxtts: 'LuxTTS',
}

const PERSONA_PLACEHOLDER =
  'Describe how this host speaks and behaves. e.g. "Calm, measured tone. Asks deep questions. Never interrupts."'

export function VoicesPanel({
  voices,
  loading,
  format,
  host1Voice,
  host2Voice,
  host3Voice,
  host1Character,
  host2Character,
  host3Character,
  onHost1Change,
  onHost2Change,
  onHost3Change,
  onHost1CharacterChange,
  onHost2CharacterChange,
  onHost3CharacterChange,
  onVoiceUploaded,
  apiBase,
}: Props) {
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [voiceName, setVoiceName] = useState('')
  const [uploadCharacter, setUploadCharacter] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const showHost2 = format !== 'brief'
  const showHost3 = format === 'ai_council_review'

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
      fd.append('character_statement', uploadCharacter.trim())
      const res = await fetch(`${apiBase}/voices/upload`, { method: 'POST', body: fd })
      if (!res.ok) throw new Error(await res.text() || res.statusText)
      const data = await res.json()
      const voiceId = `luxtts:${data.id}`
      onHost1Change(voiceId)
      if (showHost2) onHost2Change(voiceId)
      if (showHost3) onHost3Change(voiceId)
      // Pre-fill persona fields with the uploaded character statement
      if (uploadCharacter.trim()) {
        onHost1CharacterChange(uploadCharacter.trim())
        if (showHost2) onHost2CharacterChange(uploadCharacter.trim())
        if (showHost3) onHost3CharacterChange(uploadCharacter.trim())
      }
      onVoiceUploaded()
      setVoiceName('')
      setUploadCharacter('')
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const voiceLabel = (v: Voice) => {
    const tag = v.provider ? ` (${PROVIDER_LABELS[v.provider] ?? v.provider})` : ''
    return `${v.name}${tag}`
  }

  // Pre-fill persona from selected voice's stored character_statement
  const fillFromVoice = (voiceId: string, setter: (s: string) => void) => {
    const v = voices.find((x) => x.id === voiceId)
    if (v?.character_statement) setter(v.character_statement)
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
                Open <strong>TTS Setup</strong> to configure a provider — voices will appear here automatically.
                {showUpload && ' Or upload an MP3 below for LuxTTS voice cloning.'}
              </p>
            </div>
          ) : (
            <>
              {/* Host 1 */}
              <div className="voice-slot">
                <div className="voice-row">
                  <label>Host 1</label>
                  <select
                    value={host1Voice}
                    onChange={(e) => {
                      onHost1Change(e.target.value)
                      fillFromVoice(e.target.value, onHost1CharacterChange)
                    }}
                  >
                    {voices.map((v) => (
                      <option key={v.id} value={v.id}>{voiceLabel(v)}</option>
                    ))}
                  </select>
                </div>
                <div className="persona-field">
                  <label>Host 1 persona</label>
                  <textarea
                    className="voice-character-input"
                    placeholder={PERSONA_PLACEHOLDER}
                    value={host1Character}
                    onChange={(e) => onHost1CharacterChange(e.target.value)}
                    rows={3}
                  />
                </div>
              </div>

              {/* Host 2 */}
              {showHost2 && (
                <div className="voice-slot">
                  <div className="voice-row">
                    <label>Host 2</label>
                    <select
                      value={host2Voice}
                      onChange={(e) => {
                        onHost2Change(e.target.value)
                        fillFromVoice(e.target.value, onHost2CharacterChange)
                      }}
                    >
                      {voices.map((v) => (
                        <option key={v.id} value={v.id}>{voiceLabel(v)}</option>
                      ))}
                    </select>
                  </div>
                  <div className="persona-field">
                    <label>Host 2 persona</label>
                    <textarea
                      className="voice-character-input"
                      placeholder={PERSONA_PLACEHOLDER}
                      value={host2Character}
                      onChange={(e) => onHost2CharacterChange(e.target.value)}
                      rows={3}
                    />
                  </div>
                </div>
              )}

              {/* Host 3 */}
              {showHost3 && (
                <div className="voice-slot">
                  <div className="voice-row">
                    <label>Host 3 (Council)</label>
                    <select
                      value={host3Voice}
                      onChange={(e) => {
                        onHost3Change(e.target.value)
                        fillFromVoice(e.target.value, onHost3CharacterChange)
                      }}
                    >
                      {voices.map((v) => (
                        <option key={v.id} value={v.id}>{voiceLabel(v)}</option>
                      ))}
                    </select>
                  </div>
                  <div className="persona-field">
                    <label>Host 3 persona</label>
                    <textarea
                      className="voice-character-input"
                      placeholder={PERSONA_PLACEHOLDER}
                      value={host3Character}
                      onChange={(e) => onHost3CharacterChange(e.target.value)}
                      rows={3}
                    />
                  </div>
                </div>
              )}
            </>
          )}

          {/* LuxTTS voice upload */}
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
              <label>Character statement (optional — can also set per-host above)</label>
              <textarea
                placeholder={PERSONA_PLACEHOLDER}
                value={uploadCharacter}
                onChange={(e) => setUploadCharacter(e.target.value)}
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
            <p className="hint" style={{ marginTop: '0.5rem' }}>
              Using <strong>{PROVIDER_LABELS[activeProvider!] ?? activeProvider}</strong> voices.
              Switch in <strong>TTS Setup</strong>.
            </p>
          )}
        </>
      )}
    </div>
  )
}

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
      onHost1Change(data.id)
      if (showHost2) onHost2Change(data.id)
      if (showHost3) onHost3Change(data.id)
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

  return (
    <div>
      <h2>Voices</h2>
      {loading ? (
        <p className="hint">Loading voices…</p>
      ) : (
        <>
          {voices.length > 0 ? (
            <>
              <div className="voice-row">
                <label>Host 1</label>
                <select
                  value={host1Voice}
                  onChange={(e) => onHost1Change(e.target.value)}
                >
                  {voices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name}
                    </option>
                  ))}
                </select>
              </div>
          {showHost2 && (
            <div className="voice-row">
              <label>Host 2</label>
              <select
                value={host2Voice}
                onChange={(e) => onHost2Change(e.target.value)}
              >
                {voices.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
            </div>
          )}
          {showHost3 && (
            <div className="voice-row">
              <label>Host 3 (Council)</label>
              <select
                value={host3Voice}
                onChange={(e) => onHost3Change(e.target.value)}
              >
                {voices.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
            </div>
          )}
            </>
          ) : (
            <p className="hint">No voices yet. Upload one below.</p>
          )}
          <div className="voice-upload">
            <h3 className="voice-upload-title">Add voice</h3>
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
              placeholder="How they act, how they speak. e.g. Calm, measured tone. Speaks slowly with deliberate pauses."
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
        </>
      )}
    </div>
  )
}

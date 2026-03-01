import { useState, useRef } from 'react'
import type { Source } from '../App'

interface Props {
  sources: Source[]
  onSourcesChange: (s: Source[]) => void
  apiBase: string
}

export function SourcesPanel({ sources, onSourcesChange, apiBase }: Props) {
  const [pasting, setPasting] = useState(false)
  const [pasteText, setPasteText] = useState('')
  const [uploading, setUploading] = useState(false)
  const [urlOpen, setUrlOpen] = useState(false)
  const [urlInput, setUrlInput] = useState('')
  const [urlFetching, setUrlFetching] = useState(false)
  const [urlError, setUrlError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const addSource = (s: Source) => {
    if (sources.some((x) => x.id === s.id)) return
    onSourcesChange([...sources, s])
  }

  const removeSource = (id: string) => {
    onSourcesChange(sources.filter((s) => s.id !== id))
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch(`${apiBase}/sources/upload`, {
        method: 'POST',
        body: fd,
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      addSource({ id: data.source_id, filename: data.filename || file.name })
    } catch (err) {
      console.error(err)
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const handlePaste = async () => {
    if (!pasteText.trim()) return
    try {
      const res = await fetch(`${apiBase}/sources/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: pasteText }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      addSource({ id: data.source_id, filename: data.filename || 'pasted' })
      setPasteText('')
      setPasting(false)
    } catch (err) {
      console.error(err)
    }
  }

  const handleUrlFetch = async () => {
    if (!urlInput.trim()) return
    setUrlError(null)
    setUrlFetching(true)
    try {
      const res = await fetch(`${apiBase}/sources/url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: urlInput.trim() }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const msg = typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail.map((d: { msg?: string }) => d.msg).join(', ') : await res.text()
        throw new Error(msg || 'Failed to fetch URL')
      }
      addSource({ id: data.source_id, filename: data.filename || 'webpage' })
      setUrlInput('')
      setUrlOpen(false)
    } catch (err) {
      setUrlError(err instanceof Error ? err.message : String(err))
    } finally {
      setUrlFetching(false)
    }
  }

  return (
    <div>
      <h2>Sources</h2>
      <div className="sources-actions">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md"
          onChange={handleUpload}
          style={{ display: 'none' }}
        />
        <button
          className="btn btn-outline"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
        >
          {uploading ? 'Uploading…' : 'Upload PDF / TXT / MD'}
        </button>
        <button
          className="btn btn-outline"
          onClick={() => setPasting(!pasting)}
        >
          Paste text
        </button>
        <button
          className="btn btn-outline"
          onClick={() => setUrlOpen(!urlOpen)}
        >
          Add URL
        </button>
      </div>

      {urlOpen && (
        <div className="paste-area">
          <input
            type="url"
            placeholder="https://example.com/article"
            value={urlInput}
            onChange={(e) => { setUrlInput(e.target.value); setUrlError(null) }}
            onKeyDown={(e) => e.key === 'Enter' && handleUrlFetch()}
            className="url-input"
          />
          {urlError && <p className="url-error">{urlError}</p>}
          <button className="btn btn-primary" onClick={handleUrlFetch} disabled={urlFetching || !urlInput.trim()}>
            {urlFetching ? 'Fetching…' : 'Add from URL'}
          </button>
        </div>
      )}

      {pasting && (
        <div className="paste-area">
          <textarea
            placeholder="Paste your text here…"
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
            rows={4}
          />
          <button className="btn btn-primary" onClick={handlePaste}>
            Add as source
          </button>
        </div>
      )}

      <ul className="source-list">
        {sources.map((s) => (
          <li key={s.id}>
            <span className="source-name">{s.filename}</span>
            <button
              className="btn-remove"
              onClick={() => removeSource(s.id)}
              aria-label="Remove"
            >
              ×
            </button>
          </li>
        ))}
      </ul>
      {sources.length === 0 && (
        <p className="hint">Add documents or paste text to generate an overview.</p>
      )}
    </div>
  )
}

interface GenerateResult {
  status: string
  script?: string
  audio_url?: string
}

interface Props {
  onGenerate: () => void
  status: 'idle' | 'loading' | 'done' | 'error'
  result: unknown
  error: string | null
}

export function PreviewPanel({ onGenerate, status, result, error }: Props) {
  const res = result as GenerateResult | null

  return (
    <div>
      <h2>Preview & Generate</h2>
      <button
        className="btn btn-primary btn-generate"
        onClick={onGenerate}
        disabled={status === 'loading'}
      >
        {status === 'loading' ? 'Generating…' : 'Generate Audio Overview'}
      </button>

      {status === 'error' && error && (
        <div className="result-error">{error}</div>
      )}

      {status === 'done' && res?.status === 'ok' && (
        <div className="result-box">
          {res.audio_url && (
            <div className="audio-player">
              <audio controls src={res.audio_url}>
                Your browser does not support audio playback.
              </audio>
              <a href={res.audio_url} download="overview.wav" className="btn btn-outline" style={{ marginTop: '0.5rem' }}>
                Download WAV
              </a>
            </div>
          )}
          {res.script && (
            <details className="script-details">
              <summary>Script</summary>
              <pre className="script-text">{res.script}</pre>
            </details>
          )}
        </div>
      )}

      {status === 'idle' && (
        <p className="hint">
          Add sources, pick a format and voices, then generate. Uses LuxTTS for voice.
        </p>
      )}
    </div>
  )
}

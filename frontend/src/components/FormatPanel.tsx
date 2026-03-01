import type { FormatType } from '../App'

interface Props {
  format: FormatType
  onFormatChange: (f: FormatType) => void
  customPrompt: string
  onCustomPromptChange: (s: string) => void
}

const FORMATS: { id: FormatType; label: string; desc: string }[] = [
  { id: 'deep_dive', label: 'Deep Dive', desc: 'Two hosts unpack and connect topics' },
  { id: 'brief', label: 'The Brief', desc: 'Single speaker, under 2 min' },
  { id: 'critique', label: 'The Critique', desc: 'Constructive feedback on material' },
  { id: 'debate', label: 'The Debate', desc: 'Multiple perspectives' },
  { id: 'ai_council_review', label: 'AI Council Review', desc: 'All three cloud providers review and debate' },
]

export function FormatPanel({
  format,
  onFormatChange,
  customPrompt,
  onCustomPromptChange,
}: Props) {
  return (
    <div>
      <h2>Format</h2>
      <div className="format-options">
        {FORMATS.map((f) => (
          <label key={f.id} className={`format-option ${format === f.id ? 'selected' : ''}`}>
            <input
              type="radio"
              name="format"
              value={f.id}
              checked={format === f.id}
              onChange={() => onFormatChange(f.id)}
            />
            <span className="format-label">{f.label}</span>
            <span className="format-desc">{f.desc}</span>
          </label>
        ))}
      </div>
      <div className="custom-prompt">
        <label htmlFor="custom-prompt">Focus (optional)</label>
        <textarea
          id="custom-prompt"
          placeholder="e.g. Emphasize the technical implementation details…"
          value={customPrompt}
          onChange={(e) => onCustomPromptChange(e.target.value)}
          rows={2}
        />
      </div>
    </div>
  )
}

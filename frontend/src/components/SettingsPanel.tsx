import { useState, useEffect, useCallback } from 'react'

interface PromptField {
  key: string
  label: string
  description: string
  rows?: number
}

interface PromptSection {
  title: string
  fields: PromptField[]
}

const SECTIONS: PromptSection[] = [
  {
    title: 'Script Generation',
    fields: [
      {
        key: 'scriptwriter_role',
        label: 'Scriptwriter Role',
        description: 'Core identity prompt — tells the LLM what it is and what its job is before writing any script.',
        rows: 3,
      },
      {
        key: 'script_output_instructions',
        label: 'Output Instructions',
        description: 'Format rules for the script — how to label speakers, how long to make it, and what to avoid.',
        rows: 3,
      },
    ],
  },
  {
    title: 'Format Instructions',
    fields: [
      {
        key: 'format_deep_dive',
        label: 'Deep Dive',
        description: 'Instruction injected when the "Deep Dive" format is selected.',
        rows: 2,
      },
      {
        key: 'format_brief',
        label: 'Brief',
        description: 'Instruction injected when the "Brief" format is selected.',
        rows: 2,
      },
      {
        key: 'format_critique',
        label: 'Critique',
        description: 'Instruction injected when the "Critique" format is selected.',
        rows: 2,
      },
      {
        key: 'format_debate',
        label: 'Debate',
        description: 'Instruction injected when the "Debate" format is selected.',
        rows: 2,
      },
    ],
  },
  {
    title: 'AI Council Review — Round 1 (Analysis)',
    fields: [
      {
        key: 'council_intro',
        label: 'Council Intro',
        description: 'Opening context block sent to all three counselors before the review begins.',
        rows: 3,
      },
      {
        key: 'council_r1_gemini',
        label: 'Host A (Gemini) — Initial Analysis',
        description: "Gemini's first-round instruction: how to open the analysis.",
        rows: 3,
      },
      {
        key: 'council_r1_grok',
        label: 'Host B (Grok) — Initial Analysis',
        description: "Grok's first-round instruction: how to respond to Gemini's opening.",
        rows: 3,
      },
      {
        key: 'council_r1_openai',
        label: 'Host C (OpenAI) — Initial Analysis',
        description: "OpenAI's first-round instruction: how to synthesize the first two perspectives.",
        rows: 3,
      },
    ],
  },
  {
    title: 'AI Council Review — Round 2 (Debate)',
    fields: [
      {
        key: 'council_r2_gemini',
        label: 'Host A (Gemini) — Debate',
        description: "Gemini's second-round instruction: how to push back or expand.",
        rows: 3,
      },
      {
        key: 'council_r2_grok',
        label: 'Host B (Grok) — Debate',
        description: "Grok's second-round instruction: debate contribution.",
        rows: 3,
      },
      {
        key: 'council_r2_openai',
        label: 'Host C (OpenAI) — Debate',
        description: "OpenAI's second-round instruction: synthesize and propose conclusion.",
        rows: 3,
      },
    ],
  },
  {
    title: 'Chat — AI Council Personalities',
    fields: [
      {
        key: 'council_chat_gemini',
        label: 'Gemini Personality',
        description: 'The personality/role appended to Gemini in AI Council chat mode.',
        rows: 3,
      },
      {
        key: 'council_chat_grok',
        label: 'Grok Personality',
        description: 'The personality/role appended to Grok in AI Council chat mode.',
        rows: 3,
      },
      {
        key: 'council_chat_openai',
        label: 'OpenAI Personality',
        description: 'The personality/role appended to OpenAI in AI Council chat mode.',
        rows: 3,
      },
    ],
  },
  {
    title: 'Chat',
    fields: [
      {
        key: 'chat_base_system',
        label: 'Chat Base System',
        description: 'Instruction appended to every chat conversation (after the conversation history). Defines assistant behavior.',
        rows: 3,
      },
    ],
  },
]

interface Props {
  onClose: () => void
  apiBase: string
}

type PromptMap = Record<string, string>

export function SettingsPanel({ onClose, apiBase }: Props) {
  const [current, setCurrent] = useState<PromptMap>({})
  const [defaults, setDefaults] = useState<PromptMap>({})
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)

  const [enhancing, setEnhancing] = useState<Record<string, boolean>>({})
  const [enhanceErrors, setEnhanceErrors] = useState<Record<string, string>>({})

  const load = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try {
      const res = await fetch(`${apiBase}/prompts`)
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setCurrent(data.prompts || {})
      setDefaults(data.defaults || {})
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [apiBase])

  useEffect(() => {
    load()
  }, [load])

  const handleChange = (key: string, value: string) => {
    setCurrent((prev) => ({ ...prev, [key]: value }))
    setSaveMsg(null)
  }

  const handleSave = async () => {
    setSaving(true)
    setSaveMsg(null)
    try {
      const res = await fetch(`${apiBase}/prompts`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompts: current }),
      })
      if (!res.ok) throw new Error(await res.text())
      setSaveMsg('Saved.')
      setTimeout(() => setSaveMsg(null), 3000)
    } catch (e) {
      setSaveMsg(`Error: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    if (!confirm('Reset all prompts to defaults? Any customizations will be lost.')) return
    try {
      const res = await fetch(`${apiBase}/prompts/reset`, { method: 'POST' })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setCurrent(data.prompts || {})
      setDefaults(data.defaults || {})
      setSaveMsg('Reset to defaults.')
      setTimeout(() => setSaveMsg(null), 3000)
    } catch (e) {
      setSaveMsg(`Error: ${e instanceof Error ? e.message : String(e)}`)
    }
  }

  const handleEnhance = async (key: string, description: string) => {
    const text = current[key] || ''
    if (!text.trim()) return
    setEnhancing((prev) => ({ ...prev, [key]: true }))
    setEnhanceErrors((prev) => ({ ...prev, [key]: '' }))
    try {
      const res = await fetch(`${apiBase}/prompts/enhance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, context: description }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const msg = typeof data.detail === 'string' ? data.detail : 'Enhancement failed'
        throw new Error(msg)
      }
      if (data.enhanced) {
        setCurrent((prev) => ({ ...prev, [key]: data.enhanced }))
        setSaveMsg(null)
      }
    } catch (e) {
      setEnhanceErrors((prev) => ({ ...prev, [key]: e instanceof Error ? e.message : String(e) }))
    } finally {
      setEnhancing((prev) => ({ ...prev, [key]: false }))
    }
  }

  const isDirty = (key: string) => current[key] !== defaults[key]

  return (
    <div className="settings-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="settings-panel">
        {/* Header */}
        <div className="settings-header">
          <div className="settings-header-left">
            <h2>Prompt Settings</h2>
            <p className="settings-subtitle">
              Edit every prompt sent to the LLM. Click <strong>Enhance</strong> on any field to have an AI rewrite it.
            </p>
          </div>
          <button className="btn-icon settings-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        {/* Top actions */}
        <div className="settings-top-actions">
          <button className="btn btn-primary" onClick={handleSave} disabled={saving || loading}>
            {saving ? 'Saving…' : 'Save All'}
          </button>
          <button className="btn btn-outline" onClick={handleReset} disabled={loading}>
            Reset to Defaults
          </button>
          {saveMsg && (
            <span className={`settings-save-msg ${saveMsg.startsWith('Error') ? 'settings-save-error' : 'settings-save-ok'}`}>
              {saveMsg}
            </span>
          )}
        </div>

        {/* Body */}
        <div className="settings-body">
          {loading && <p className="settings-loading">Loading prompts…</p>}
          {loadError && <p className="settings-load-error">{loadError}</p>}

          {!loading && !loadError && SECTIONS.map((section) => (
            <div key={section.title} className="settings-section">
              <h3 className="settings-section-title">{section.title}</h3>
              {section.fields.map((field) => (
                <div key={field.key} className="settings-field">
                  <div className="settings-field-header">
                    <div>
                      <label className="settings-label">
                        {field.label}
                        {isDirty(field.key) && <span className="settings-dirty-dot" title="Modified" />}
                      </label>
                      <p className="settings-field-desc">{field.description}</p>
                    </div>
                    <button
                      className="btn btn-outline settings-enhance-btn"
                      onClick={() => handleEnhance(field.key, field.description)}
                      disabled={enhancing[field.key] || !current[field.key]?.trim()}
                      title="Use AI to improve this prompt"
                    >
                      {enhancing[field.key] ? (
                        <span className="settings-enhance-spinner" />
                      ) : (
                        '✦ Enhance'
                      )}
                    </button>
                  </div>
                  <textarea
                    className="settings-textarea"
                    rows={field.rows ?? 3}
                    value={current[field.key] ?? ''}
                    onChange={(e) => handleChange(field.key, e.target.value)}
                    spellCheck={false}
                  />
                  {enhanceErrors[field.key] && (
                    <p className="settings-enhance-error">{enhanceErrors[field.key]}</p>
                  )}
                  {isDirty(field.key) && (
                    <button
                      className="settings-reset-field-btn"
                      onClick={() => handleChange(field.key, defaults[field.key] ?? '')}
                    >
                      ↩ Restore default
                    </button>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

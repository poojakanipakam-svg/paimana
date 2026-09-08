import { useEffect, useRef, useState } from 'react'
import { api } from '../api'

export default function Assistant() {
  const [msgs, setMsgs] = useState<{ role: 'user' | 'bot'; text: string; engine?: string; model?: string }[]>([{
    role: 'bot',
    text: 'Namaste! I am the PAIMANA assistant. Ask me about MoSPI central-sector projects — risk rankings, sector/ministry/state aggregates, cost & schedule overruns, model drivers, data quality, or specific projects.\n\nExamples: "top 10 riskiest projects", "cost overrun in Railways", "tell me about project N24001451".',
  }])
  const [q, setQ] = useState('')
  const [busy, setBusy] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs])

  const ask = async (text?: string) => {
    const question = (text ?? q).trim()
    if (!question || busy) return
    setMsgs(m => [...m, { role: 'user', text: question }])
    setQ(''); setBusy(true)
    try {
      const r = await api(`/api/assistant?q=${encodeURIComponent(question)}`)
      setMsgs(m => [...m, { role: 'bot', text: r.answer, engine: r.engine, model: r.model }])
    } catch (e: any) {
      setMsgs(m => [...m, { role: 'bot', text: `Sorry, an error occurred: ${e.message}` }])
    }
    setBusy(false)
  }

  const suggestions = ['Top 10 riskiest projects', 'Cost overrun in Railways sector',
    'Projects in Maharashtra', 'What drives the model', 'Data quality and sources']

  return <div className="page" style={{ maxWidth: 860 }}>
    <div className="card chat" style={{ minHeight: 420 }}>
      {msgs.map((m, i) => <div key={i}>
        <div className={`msg ${m.role}`}>{m.text}</div>
        {m.role === 'bot' && i > 0 && m.engine && <div style={{ fontSize: 10.5, color: '#6b7280', margin: '-6px 0 10px 2px' }}>
          {m.engine === 'gemini'
            ? `✦ answered by ${m.model || 'Gemini'} · facts retrieved from the PAIMANA database (tool-grounded)`
            : '⚙ answered by the built-in deterministic engine · facts computed from the PAIMANA database'}
        </div>}
      </div>)}
      {busy && <div className="msg bot">Thinking…</div>}
      <div ref={endRef} />
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 4 }}>
        {suggestions.map(s => <button key={s} className="tag-sim" style={{
          background: '#fff', cursor: 'pointer', fontSize: 11.5,
        }} onClick={() => ask(s)}>{s}</button>)}
      </div>
      <div className="chat-input">
        <input value={q} onChange={e => setQ(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && ask()}
          placeholder="Ask about projects, sectors, overruns, risk…" />
        <button onClick={() => ask()} disabled={busy}>Ask</button>
      </div>
      <div className="note" style={{ marginTop: 8 }}>
        Answers are grounded in the MoSPI panel of the PAIMANA database — the Gemini
        layer (when enabled) must call database tools for every fact, and a
        deterministic engine serves as fallback. The assistant does not state or imply official government
        decisions; where data is insufficient it says so explicitly.
      </div>
    </div>
  </div>
}

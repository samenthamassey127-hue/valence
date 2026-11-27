import { useEffect, useRef, useState } from 'react'
import {
  Check,
  Copy,
  Download,
  FileText,
  Globe,
  Headphones,
  Mic,
  Scale,
  Settings,
  ShieldCheck,
  Sparkles,
  Square,
  Trash2,
  Volume2,
  X,
} from 'lucide-react'

const LANGUAGES = [
  { code: 'en-IN', speechCode: 'en-IN', label: 'English (IN)' },
  { code: 'hinglish', speechCode: 'hi-IN', label: 'Hinglish' },
  { code: 'hi-IN', speechCode: 'hi-IN', label: 'हिन्दी (Hindi)' },
  { code: 'ta-IN', speechCode: 'ta-IN', label: 'தமிழ் (Tamil)' },
  { code: 'mr-IN', speechCode: 'mr-IN', label: 'मराठी (Marathi)' },
  { code: 'te-IN', speechCode: 'te-IN', label: 'తెలుగు (Telugu)' },
  { code: 'bn-IN', speechCode: 'bn-IN', label: 'বাংলা (Bengali)' },
]

const SAMPLE_VOICES = [
  {
    lang: 'hinglish',
    text: 'Subah municipal lineman ne bina notice water connection kaat diya aur 3000 cash maang raha hai, jabki bill paid hai.',
  },
  {
    lang: 'hi-IN',
    text: 'बिजली विभाग के लाइनमैन ने बिना किसी नोटिस के हमारा मीटर काट दिया और 2000 रुपये नकद मांग रहा है।',
  },
  {
    lang: 'ta-IN',
    text: 'போக்குவரத்து காவலர் என் வாகன சாவியை எடுத்துவிட்டு ரசீது இல்லாமல் 1500 ரூபாய் கேட்கிறார்.',
  },
  {
    lang: 'mr-IN',
    text: 'तहसील कार्यालयात माझे उत्पन्न प्रमाणपत्र १५ दिवसांपासून अडवले आहे आणि कारकून ५०० रुपये रोख मागत आहे.',
  },
  {
    lang: 'en-IN',
    text: 'The traffic officer at MG Road signal seized my bike keys and demanded 1500 cash without an e-Challan receipt.',
  },
]

const DEFAULT_BARS = [24, 42, 68, 36, 80, 52, 30, 62, 44, 28]

export default function App() {
  const [view, setView] = useState('speak') // 'speak' | 'ledger' | 'statutes'
  const [language, setLanguage] = useState('hinglish')
  const [transcript, setTranscript] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [bars, setBars] = useState(DEFAULT_BARS)
  const [noiseWarning, setNoiseWarning] = useState(false)
  const [clarification, setClarification] = useState(null)
  const [activeCase, setActiveCase] = useState(null)
  const [cardTab, setCardTab] = useState('inear') // 'inear' | 'rti' | 'grievance'
  const [cases, setCases] = useState([])
  const [statutes, setStatutes] = useState([])
  const [copied, setCopied] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [showTranscriptBox, setShowTranscriptBox] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [geminiKey, setGeminiKey] = useState(() => localStorage.getItem('valence_gemini_key') || '')
  const [sampleIdx, setSampleIdx] = useState(0)

  const recognitionRef = useRef(null)
  const audioCtxRef = useRef(null)
  const animFrameRef = useRef(null)
  const streamRef = useRef(null)
  const transcriptRef = useRef('')

  useEffect(() => {
    fetchCases()
    fetchStatutes()
    return () => {
      stopAudioMonitoring()
      window.speechSynthesis?.cancel()
    }
  }, [])

  async function fetchCases() {
    try {
      const res = await fetch('/api/cases')
      const data = await res.json()
      setCases(data.cases || [])
    } catch {
      // Backend offline fallback handled silently
    }
  }

  async function fetchStatutes() {
    try {
      const res = await fetch('/api/statutes')
      const data = await res.json()
      setStatutes(data.statutes || [])
    } catch {
      // Ignore
    }
  }

  function speakText(text, langCode) {
    if (!window.speechSynthesis || !text) return
    window.speechSynthesis.cancel()

    const target = LANGUAGES.find((l) => l.code === langCode)?.speechCode || 'en-IN'
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = target
    utterance.rate = 0.98

    const voices = window.speechSynthesis.getVoices()
    const match =
      voices.find((v) => v.lang.toLowerCase() === target.toLowerCase()) ||
      voices.find((v) => v.lang.toLowerCase().startsWith(target.split('-')[0].toLowerCase()))
    if (match) utterance.voice = match

    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)
    window.speechSynthesis.speak(utterance)
  }

  function stopSpeaking() {
    window.speechSynthesis?.cancel()
    setIsSpeaking(false)
  }

  async function startAudioMonitoring() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      const ctx = new AudioCtx()
      audioCtxRef.current = ctx
      const source = ctx.createMediaStreamSource(stream)
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 32
      source.connect(analyser)

      const dataArray = new Uint8Array(analyser.frequencyBinCount)
      const tick = () => {
        analyser.getByteFrequencyData(dataArray)
        const nextBars = Array.from({ length: 10 }, (_, idx) => {
          const val = dataArray[idx % dataArray.length] || 0
          return Math.max(16, Math.min(100, Math.round((val / 255) * 100)))
        })
        setBars(nextBars)
        const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length
        setNoiseWarning(avg > 175)
        animFrameRef.current = requestAnimationFrame(tick)
      }
      tick()
    } catch {
      // Mic permission declined or unavailable; keep text fallback active
    }
  }

  function stopAudioMonitoring() {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {})
      audioCtxRef.current = null
    }
    setBars(DEFAULT_BARS)
    setNoiseWarning(false)
  }

  function toggleListening() {
    if (isListening) {
      stopListeningAndAnalyze()
      return
    }

    stopSpeaking()
    setShowTranscriptBox(true)
    setClarification(null)

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRec) {
      // Clean fallback if browser lacks Web Speech API
      setIsListening(false)
      return
    }

    const rec = new SpeechRec()
    const speechLang = LANGUAGES.find((l) => l.code === language)?.speechCode || 'en-IN'
    rec.lang = speechLang
    rec.continuous = true
    rec.interimResults = true

    const baseText = clarification ? `${transcriptRef.current} ` : ''
    if (!clarification) {
      transcriptRef.current = ''
      setTranscript('')
    }

    rec.onresult = (event) => {
      let interim = ''
      let finalChunk = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const piece = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalChunk += `${piece} `
        } else {
          interim += piece
        }
      }
      if (finalChunk) {
        transcriptRef.current = `${baseText}${finalChunk}`.trim()
      }
      const display = `${transcriptRef.current} ${interim}`.trim()
      setTranscript(display)
    }

    rec.onerror = () => {
      setIsListening(false)
      stopAudioMonitoring()
    }

    rec.onend = () => {
      setIsListening(false)
      stopAudioMonitoring()
    }

    recognitionRef.current = rec
    rec.start()
    setIsListening(true)
    startAudioMonitoring()
  }

  function stopListeningAndAnalyze() {
    try {
      recognitionRef.current?.stop()
    } catch {
      // Ignore
    }
    setIsListening(false)
    stopAudioMonitoring()
    const finalSpoken = transcript.trim() || transcriptRef.current.trim()
    if (finalSpoken) {
      runAnalyze(finalSpoken, language)
    }
  }

  async function runAnalyze(textInput, targetLang = language) {
    if (!textInput.trim()) return
    setIsAnalyzing(true)
    setClarification(null)
    try {
      const headers = { 'Content-Type': 'application/json' }
      if (geminiKey.trim()) headers['X-Gemini-Key'] = geminiKey.trim()

      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          transcript: textInput,
          language: targetLang,
          auto_save: true,
        }),
      })
      const data = await res.json()

      if (data.needs_clarification) {
        setClarification(data.clarification_question)
        speakText(data.clarification_question, targetLang)
      } else {
        setActiveCase(data)
        setCardTab('inear')
        speakText(data.in_ear_script, targetLang)
        fetchCases()
      }
    } finally {
      setIsAnalyzing(false)
    }
  }

  function handleDemoVoice() {
    stopSpeaking()
    const sample = SAMPLE_VOICES[sampleIdx % SAMPLE_VOICES.length]
    setSampleIdx((i) => i + 1)
    setLanguage(sample.lang)
    setTranscript(sample.text)
    transcriptRef.current = sample.text
    setShowTranscriptBox(true)
    runAnalyze(sample.text, sample.lang)
  }

  async function handleStatusCycle(item) {
    const order = ['Drafted', 'RTI Filed', 'Resolved']
    const next = order[(order.indexOf(item.status) + 1) % order.length]
    const res = await fetch(`/api/cases/${item.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: next }),
    })
    if (res.ok) {
      fetchCases()
      if (activeCase?.id === item.id) {
        setActiveCase({ ...activeCase, status: next })
      }
    }
  }

  async function handleDeleteCase(id) {
    const res = await fetch(`/api/cases/${id}`, { method: 'DELETE' })
    if (res.ok) {
      fetchCases()
      if (activeCase?.id === id) setActiveCase(null)
    }
  }

  function copyCurrentTab() {
    if (!activeCase) return
    const text =
      cardTab === 'inear'
        ? activeCase.in_ear_script
        : cardTab === 'rti'
          ? activeCase.rti_draft
          : activeCase.grievance_draft
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }

  function saveSettings() {
    localStorage.setItem('valence_gemini_key', geminiKey.trim())
    setShowSettings(false)
  }

  return (
    <div className="valence-canvas">
      <div className="ambient-mesh" />
      <div className="fluted-lines" />

      <div className="shell">
        {/* Top Floating Navbar */}
        <header className="topbar">
          <div className="brand" onClick={() => setView('speak')}>
            <svg width="22" height="14" viewBox="0 0 22 14" fill="none">
              <path
                d="M1 7C3.5 2 6.5 2 9 7C11.5 12 14.5 12 17 7C18.5 4 20 3 21 3"
                stroke="#E09F3E"
                strokeWidth="2.2"
                strokeLinecap="round"
              />
            </svg>
            <span>VALENCE</span>
          </div>

          <nav className="nav-pill" aria-label="Primary navigation">
            <button
              className={`nav-btn ${view === 'speak' ? 'active' : ''}`}
              onClick={() => setView('speak')}
            >
              Speak
            </button>
            <button
              className={`nav-btn ${view === 'ledger' ? 'active' : ''}`}
              onClick={() => {
                fetchCases()
                setView('ledger')
              }}
            >
              Ledger ({cases.length})
            </button>
            <button
              className={`nav-btn ${view === 'statutes' ? 'active' : ''}`}
              onClick={() => setView('statutes')}
            >
              Statutes
            </button>
          </nav>

          <div className="topbar-right">
            <select
              className="lang-select"
              aria-label="Regional language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
            <button
              className="icon-pill"
              title="Engine Settings"
              onClick={() => setShowSettings(true)}
            >
              <Settings size={15} />
            </button>
          </div>
        </header>

        {/* SPEAK HERO VIEW */}
        {view === 'speak' && (
          <main className="hero-grid">
            {/* Left Editorial Column */}
            <div>
              <h1 className="hero-title">
                Speak once.
                <br />
                Make them answer.
              </h1>
              <p className="hero-sub">
                Regional voice to Section 20 RTI leverage & live audio defense.
              </p>

              <div className="cta-row">
                <button
                  className={`btn-primary ${isListening ? 'listening' : ''}`}
                  onClick={toggleListening}
                >
                  {isListening ? <Square size={15} /> : <Mic size={16} />}
                  <span>
                    {isListening
                      ? 'Stop & Generate'
                      : isAnalyzing
                        ? 'Building Dossier...'
                        : 'Tap to Speak'}
                  </span>
                </button>

                <button className="btn-secondary" onClick={handleDemoVoice}>
                  <Sparkles size={15} />
                  <span>Demo Regional Voice</span>
                </button>
              </div>

              {(showTranscriptBox || transcript) && (
                <div className="voice-box">
                  <div className="voice-box-header">
                    <span>
                      {isListening
                        ? noiseWarning
                          ? 'High street noise — speak closer'
                          : 'Listening in ' +
                            (LANGUAGES.find((l) => l.code === language)?.label || language)
                        : 'Voice Transcript'}
                    </span>
                    <div className="wave-bars">
                      {bars.map((h, idx) => (
                        <div
                          key={idx}
                          className="wave-bar"
                          style={{ height: `${isListening ? Math.max(18, h) : 20}%` }}
                        />
                      ))}
                    </div>
                  </div>

                  <textarea
                    className="transcript-input"
                    rows={3}
                    value={transcript}
                    onChange={(e) => {
                      setTranscript(e.target.value)
                      transcriptRef.current = e.target.value
                    }}
                    placeholder="Speak or type your issue in any regional language..."
                  />

                  <div className="voice-box-footer">
                    <span style={{ fontSize: '12px', color: 'rgba(244,237,224,0.55)' }}>
                      Editable before filing
                    </span>
                    <button
                      className="btn-secondary"
                      style={{ padding: '7px 14px', fontSize: '12px' }}
                      onClick={() => runAnalyze(transcript, language)}
                      disabled={!transcript.trim() || isAnalyzing}
                    >
                      {isAnalyzing ? 'Generating...' : 'Generate RTI →'}
                    </button>
                  </div>
                </div>
              )}

              {clarification && (
                <div className="clarify-banner">
                  <Volume2 size={16} color="#E09F3E" style={{ flexShrink: 0 }} />
                  <span>{clarification}</span>
                </div>
              )}
            </div>

            {/* Right Floating Frosted Glass Card */}
            <section className="glass-card">
              {!activeCase ? (
                <>
                  <div className="card-top-row">
                    <span>Statutory Shield Active</span>
                    <span className="statute-pill">
                      <ShieldCheck size={12} /> Ready
                    </span>
                  </div>

                  <div className="inner-tile" onClick={handleDemoVoice}>
                    <div>
                      <div className="tile-title">RTI Act · Section 20</div>
                      <div className="tile-meta">Officer personal salary deduction</div>
                    </div>
                    <div className="tile-metric">₹250/day</div>
                  </div>

                  <div className="inner-tile" onClick={handleDemoVoice}>
                    <div>
                      <div className="tile-title">Citizen Charter SLA</div>
                      <div className="tile-meta">Utility & civic resolution window</div>
                    </div>
                    <div className="tile-metric">48 hrs</div>
                  </div>

                  <div className="inner-tile" onClick={() => setView('ledger')}>
                    <div>
                      <div className="tile-title">Saved Case Ledger</div>
                      <div className="tile-meta">Persisted in SQLite database</div>
                    </div>
                    <div className="tile-metric">{cases.length}</div>
                  </div>

                  <button
                    className="btn-primary"
                    style={{ width: '100%', justifyContent: 'center', marginTop: '6px' }}
                    onClick={toggleListening}
                  >
                    <Mic size={16} />
                    <span>Start Voice Shield →</span>
                  </button>
                </>
              ) : (
                <>
                  <div className="card-top-row">
                    <span style={{ fontWeight: 600, color: '#F4EDE0' }}>
                      {activeCase.case_code} · {activeCase.department}
                    </span>
                    <span className="statute-pill">{activeCase.sla_days}d SLA</span>
                  </div>

                  <div
                    style={{
                      fontSize: '12px',
                      color: 'rgba(244,237,224,0.72)',
                      marginBottom: '12px',
                    }}
                  >
                    {activeCase.statute_ref}
                    {activeCase.extortion_amount ? ` · Demand: ${activeCase.extortion_amount}` : ''}
                  </div>

                  <div className="card-tabs">
                    <button
                      className={`card-tab ${cardTab === 'inear' ? 'active' : ''}`}
                      onClick={() => setCardTab('inear')}
                    >
                      In-Ear Script
                    </button>
                    <button
                      className={`card-tab ${cardTab === 'rti' ? 'active' : ''}`}
                      onClick={() => setCardTab('rti')}
                    >
                      RTI Form-A
                    </button>
                    <button
                      className={`card-tab ${cardTab === 'grievance' ? 'active' : ''}`}
                      onClick={() => setCardTab('grievance')}
                    >
                      CPGRAMS
                    </button>
                  </div>

                  <div className="dossier-body">
                    {cardTab === 'inear' ? (
                      <div className="in-ear-quote">“{activeCase.in_ear_script}”</div>
                    ) : cardTab === 'rti' ? (
                      activeCase.rti_draft
                    ) : (
                      activeCase.grievance_draft
                    )}
                  </div>

                  <div className="card-actions">
                    <button
                      className="btn-primary"
                      style={{ padding: '10px 16px', fontSize: '13px' }}
                      onClick={() =>
                        isSpeaking
                          ? stopSpeaking()
                          : speakText(activeCase.in_ear_script, activeCase.language)
                      }
                    >
                      <Volume2 size={15} />
                      <span>{isSpeaking ? 'Stop Audio' : 'Play Voice'}</span>
                    </button>

                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        className="btn-secondary"
                        style={{ padding: '9px 14px', fontSize: '12px' }}
                        onClick={copyCurrentTab}
                      >
                        {copied ? <Check size={14} /> : <Copy size={14} />}
                        <span>{copied ? 'Copied' : 'Copy'}</span>
                      </button>

                      {activeCase.id && (
                        <a
                          href={`/api/cases/${activeCase.id}/export`}
                          className="btn-secondary"
                          style={{ padding: '9px 14px', fontSize: '12px', textDecoration: 'none' }}
                        >
                          <Download size={14} />
                          <span>Export</span>
                        </a>
                      )}
                    </div>
                  </div>
                </>
              )}
            </section>
          </main>
        )}

        {/* LEDGER VIEW (SQLite Persistence) */}
        {view === 'ledger' && (
          <main className="panel-section">
            <div className="section-header">
              <div>
                <h2 className="serif-display" style={{ fontSize: '34px', fontWeight: 400 }}>
                  Case Ledger
                </h2>
              </div>
              <button className="btn-primary" onClick={() => setView('speak')}>
                <Mic size={15} />
                <span>New Voice Case</span>
              </button>
            </div>

            <div className="cards-grid">
              {cases.map((item) => (
                <div key={item.id} className="glass-card" style={{ padding: '18px' }}>
                  <div className="card-top-row" style={{ marginBottom: '10px' }}>
                    <span style={{ fontWeight: 700, color: '#F4EDE0' }}>{item.case_code}</span>
                    <button
                      className={`status-badge ${
                        item.status === 'RTI Filed'
                          ? 'filed'
                          : item.status === 'Resolved'
                            ? 'resolved'
                            : ''
                      }`}
                      onClick={() => handleStatusCycle(item)}
                      title="Click to advance status"
                    >
                      {item.status}
                    </button>
                  </div>

                  <div className="tile-title" style={{ marginBottom: '6px' }}>
                    {item.department}
                  </div>
                  <div
                    style={{
                      fontSize: '13px',
                      color: 'rgba(244,237,224,0.75)',
                      lineHeight: 1.5,
                      marginBottom: '14px',
                    }}
                  >
                    “{item.transcript}”
                  </div>

                  <div className="card-actions" style={{ marginTop: 'auto' }}>
                    <button
                      className="btn-secondary"
                      style={{ padding: '7px 12px', fontSize: '12px' }}
                      onClick={() => {
                        setActiveCase(item)
                        setCardTab('rti')
                        setView('speak')
                      }}
                    >
                      <FileText size={13} />
                      <span>Open</span>
                    </button>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <a
                        href={`/api/cases/${item.id}/export`}
                        className="icon-pill"
                        title="Download dossier"
                      >
                        <Download size={14} />
                      </a>
                      <button
                        className="icon-pill"
                        title="Delete case"
                        onClick={() => handleDeleteCase(item.id)}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </main>
        )}

        {/* STATUTES VIEW */}
        {view === 'statutes' && (
          <main className="panel-section">
            <div className="section-header">
              <h2 className="serif-display" style={{ fontSize: '34px', fontWeight: 400 }}>
                Indexed Indian Statutes
              </h2>
              <button className="btn-secondary" onClick={() => setView('speak')}>
                Back to Voice
              </button>
            </div>

            <div className="cards-grid">
              {statutes.map((st) => (
                <div key={st.id} className="glass-card" style={{ padding: '18px' }}>
                  <div className="card-top-row" style={{ marginBottom: '8px' }}>
                    <span className="statute-pill">{st.sla_days}d SLA</span>
                    <span>{st.department}</span>
                  </div>
                  <div className="tile-title" style={{ fontSize: '15px', marginBottom: '8px' }}>
                    {st.violation_title}
                  </div>
                  <div style={{ fontSize: '12px', color: 'rgba(244,237,224,0.72)', lineHeight: 1.55 }}>
                    {st.statute_ref}
                  </div>
                </div>
              ))}
            </div>
          </main>
        )}

        {/* Bottom Feature Strip */}
        <footer className="bottom-strip">
          <div className="strip-item">
            <Globe size={16} />
            <span>7 Regional Voices</span>
          </div>
          <div className="strip-item">
            <Scale size={16} />
            <span>Section 20 RTI</span>
          </div>
          <div className="strip-item">
            <Headphones size={16} />
            <span>In-Ear Audio Defense</span>
          </div>
          <div className="strip-item">
            <ShieldCheck size={16} />
            <span>SQLite Case Ledger</span>
          </div>
        </footer>
      </div>

      {/* Optional API Key Modal */}
      {showSettings && (
        <div className="modal-backdrop" onClick={() => setShowSettings(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="card-top-row">
              <span style={{ fontWeight: 600, fontSize: '15px', color: '#F4EDE0' }}>
                Engine Settings
              </span>
              <button className="icon-pill" onClick={() => setShowSettings(false)}>
                <X size={14} />
              </button>
            </div>
            <label style={{ fontSize: '12px', color: 'rgba(244,237,224,0.74)' }}>
              Gemini API Key (Optional — works offline without key)
            </label>
            <input
              type="password"
              className="field-input"
              placeholder="AIza..."
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
            />
            <button
              className="btn-primary"
              style={{ width: '100%', justifyContent: 'center', marginTop: '16px' }}
              onClick={saveSettings}
            >
              Save
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

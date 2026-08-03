import { useState, useRef, useEffect } from 'react'
import './App.css'

const API_BASE = 'https://job-search-rag-backend.onrender.com'

const DOC_TYPES = [
  { value: 'general', label: 'General' },
  { value: 'resume', label: 'Resume' },
  { value: 'offer_letter', label: 'Offer Letter' },
  { value: 'jd', label: 'Job Description' },
  { value: 'policy', label: 'HR Policy' },
]

function Dropdown({ value, onChange }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const selected = DOC_TYPES.find(d => d.value === value)

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="dropdown" ref={ref}>
      <div className="dropdown-trigger" onClick={() => setOpen(!open)}>
        {selected.label}
        <span>▾</span>
      </div>
      {open && (
        <div className="dropdown-menu">
          {DOC_TYPES.map(opt => (
            <div
              key={opt.value}
              className={`dropdown-option ${opt.value === value ? 'selected' : ''}`}
              onClick={() => { onChange(opt.value); setOpen(false) }}
            >
              {opt.label}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function App() {
  const [file, setFile] = useState(null)
  const [docType, setDocType] = useState('general')
  const [uploadStatus, setUploadStatus] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setUploadStatus(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('doc_type', docType)

    try {
      const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData })
      const data = await res.json()
      setUploadStatus({ type: 'success', text: `${data.filename} uploaded successfully` })
    } catch (err) {
      setUploadStatus({ type: 'error', text: 'Upload failed. Check backend is running.' })
    } finally {
      setUploading(false)
    }
  }

  const handleAsk = async () => {
    if (!question.trim() || loading) return
    const userMessage = { role: 'user', content: question }
    setMessages(prev => [...prev, userMessage])
    setLoading(true)
    setQuestion('')

    const formData = new FormData()
    formData.append('question', question)

    try {
      const res = await fetch(`${API_BASE}/ask`, { method: 'POST', body: formData })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer, sources: data.sources }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error getting answer. Check backend is running.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <div className="header">
        <h1>Job Search Assistant</h1>
        <p>Upload your documents and get answers grounded in your own files</p>
      </div>

      <div className="card">
        <h2>📄 Upload a Document</h2>
        <div className="upload-row">
          <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} />
          <Dropdown value={docType} onChange={setDocType} />
          <button onClick={handleUpload} disabled={!file || uploading}>
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
        {uploadStatus && (
          <div className={`status ${uploadStatus.type}`}>
            {uploadStatus.type === 'success' ? '✅' : '❌'} {uploadStatus.text}
          </div>
        )}
      </div>

      <div className="card">
        <h2>💬 Ask a Question</h2>
        <div className={`chat-window ${messages.length === 0 ? 'empty' : ''}`}>
          {messages.length === 0 && (
            <div className="chat-empty">Upload a document to get started</div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="bubble">{msg.content}</div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources">Sources: {msg.sources.map(s => s.filename).join(', ')}</div>
              )}
            </div>
          ))}
          {loading && <div className="thinking">Thinking...</div>}
        </div>
        <div className="input-row">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
            placeholder="Ask a question about your documents..."
          />
          <button onClick={handleAsk} disabled={loading || !question.trim()}>Ask</button>
        </div>
      </div>
    </div>
  )
}

export default App
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import './index.css'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || `Server returned ${response.status}`)
      }

      setMessages((prev) => [...prev, { role: 'ai', content: data.reply }])
    } catch (error) {
      console.error('Chat request failed:', error)
      setMessages((prev) => [...prev, {
        role: 'ai',
        content: `Server error: ${error.message}`
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app-container">
      <h1>YouTube Finder AI</h1>
      <div className="chat-box">
        <div className="messages">
          {messages.length === 0 && <p style={{color: '#888', textAlign: 'center'}}>Ask me to find some YouTube videos!</p>}
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role === 'user' ? 'user-message' : 'ai-message'}`}>
              <strong>{msg.role === 'user' ? 'You' : 'AI Agent'}</strong>
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          ))}
          {isLoading && (
            <div className="message ai-message">
              <em>Thinking and searching...</em>
            </div>
          )}
        </div>
        
        <form onSubmit={sendMessage} className="input-container">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a topic (e.g. React tutorials)..."
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  )
}

export default App

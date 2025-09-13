import React, { useState, useEffect, useRef } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export default function App() {
  const [messages, setMessages] = useState([
    { from: 'bot', text: 'Welcome to HealthPlus Lab — ask about tests, book appointments, or get offers.' }
  ])
  const [input, setInput] = useState('')
  const [name, setName] = useState('')
  const [showBookingForm, setShowBookingForm] = useState(false)
  const [testId, setTestId] = useState('')
  const [phone, setPhone] = useState('')
  const [date, setDate] = useState('')
  const [tests, setTests] = useState([])
  const recognitionRef = useRef(null)
  const [showTestCards, setShowTestCards] = useState(false)

  useEffect(() => {
    // load tests initially
    fetch(API + '/tests')
      .then(res => res.json())
      .then(data => setTests(data.tests))
  }, [])

  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      console.warn('No speech synthesis support in this browser')
    }
  }, [])

  const speak = (text) => {
    if ('speechSynthesis' in window) {
      const ut = new SpeechSynthesisUtterance(text)
      window.speechSynthesis.cancel()
      window.speechSynthesis.speak(ut)
    }
  }

  const sendMessage = async (msg) => {
    setMessages(m => [...m, { from: 'user', text: msg }])
    setInput('')

    // detect booking
    if (msg.toLowerCase().includes('book')) {
      setShowBookingForm(true)
      setShowTestCards(false)
      setMessages(m => [...m,
        { from: 'bot', text: 'Sure! Fill out the form below to book your appointment.' }
      ])
      return
    }

    // detect test or price queries
    if (msg.toLowerCase().includes('test') || msg.toLowerCase().includes('price')) {
      if (tests.length === 0) {
        const resTests = await fetch(API + '/tests')
        const dataTests = await resTests.json()
        setTests(dataTests.tests)
      }
      setShowTestCards(true)
      setShowBookingForm(false)
      setMessages(m => [...m,
        { from: 'bot', text: 'Here are our available tests:' }
      ])
      return
    }

    // normal chat
    const res = await fetch(API + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: name, message: msg })
    })
    const data = await res.json()
    setMessages(m => [...m, { from: 'bot', text: data.reply }])
    speak(data.reply)
  }

  const startVoice = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return alert('SpeechRecognition not supported in this browser.')
    const recog = new SpeechRecognition()
    recog.lang = 'en-IN'
    recog.interimResults = false
    recog.onresult = (e) => {
      const text = e.results[0][0].transcript
      sendMessage(text)
    }
    recog.onerror = (e) => { console.error(e); alert('Voice error: ' + e.error) }
    recog.start()
    recognitionRef.current = recog
  }

  const submitBooking = async () => {
    if (!name) return alert('Please enter your name above.')
    if (!testId) return alert('Please select a test.')
    if (!phone) return alert('Please enter phone.')
    if (!date) return alert('Please select a date.')

    const res = await fetch(API + '/book', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, phone, test_id: testId, date })
    })
    const data = await res.json()
    setMessages(m => [...m, {
      from: 'bot',
      text: `✅ Booked ${data.test.name} for ${data.booking_for} on ${data.date}. Offer: ${data.offer || 'None'}`
    }])
    speak(`Booked ${data.test.name} on ${data.date}. ${data.offer || ''}`)
    setShowBookingForm(false)
    setTestId(''); setPhone(''); setDate('')
  }

  // find selected test to show price/prep
  const selectedTest = tests.find(t => t.id === testId)

  return (
    <div style={{ fontFamily: 'Arial', padding: 20, maxWidth: 800, margin: '0 auto' }}>
      <h2>HealthPlus Medical Lab — Chatbot</h2>
      <div style={{ marginBottom: 10 }}>
        <label>Your name: </label>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Optional for offers" />
        <button onClick={startVoice} style={{ marginLeft: 10 }}>🎤 Voice Chat</button>
      </div>

      <div style={{ border: '1px solid #ddd', padding: 10, height: 400, overflow: 'auto', background: '#fafafa' }}>
        {messages.map((m, i) => (
          <div key={i} style={{ textAlign: m.from === 'user' ? 'right' : 'left', margin: '8px 0' }}>
            <div style={{
              display: 'inline-block', padding: 10, borderRadius: 8,
              background: m.from === 'user' ? '#d1e7dd' : '#fff',
              boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
            }}>
              <strong style={{ display: 'block', fontSize: 12 }}>{m.from}</strong>
              <div>{m.text}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Show Test Cards */}
      {showTestCards && tests.length > 0 && (
        <div style={{ padding: 10, background: '#f9f9f9', border: '1px solid #ccc', borderRadius: 10, marginTop: 10 }}>
          <h3>🧪 Available Tests</h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px,1fr))',
            gap: 10
          }}>
            {tests.map(t => (
              <div key={t.id} style={{
                background: '#fff', padding: 10, borderRadius: 8,
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }}>
                <h4 style={{ margin: '5px 0' }}>{t.name}</h4>
                <p><strong>₹{t.price}</strong></p>
                <p style={{ fontSize: 12, color: '#555' }}>{t.prep}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Show Booking Form */}
      {showBookingForm && (
        <div style={{
          border: '1px solid #ccc', padding: 15, marginTop: 15,
          borderRadius: 10, background: '#f0f8ff'
        }}>
          <h3>📋 Book Appointment</h3>
          <div style={{ marginBottom: 10 }}>
            <label>Select Test: </label>
            <select value={testId} onChange={e => setTestId(e.target.value)}>
              <option value="">--Choose--</option>
              {tests.map(t => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>
          {selectedTest && (
            <div style={{ marginBottom: 10, background: '#fff', padding: 10, borderRadius: 8 }}>
              <p><strong>Price:</strong> ₹{selectedTest.price}</p>
              <p><strong>Preparation:</strong> {selectedTest.prep}</p>
            </div>
          )}
          <div style={{ marginBottom: 10 }}>
            <label>Phone: </label>
            <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="Phone number" />
          </div>
          <div style={{ marginBottom: 10 }}>
            <label>Date: </label>
            <input type="date" value={date} onChange={e => setDate(e.target.value)} />
          </div>
          <button onClick={submitBooking} style={{
            background: '#4CAF50', color: '#fff', padding: '8px 16px',
            border: 'none', borderRadius: 8
          }}>Book Now</button>
        </div>
      )}

      <div style={{ marginTop: 10 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') sendMessage(input) }}
          placeholder="Type a message and press Enter"
          style={{ width: '70%' }} />
        <button onClick={() => sendMessage(input)} style={{ marginLeft: 10 }}>Send</button>
      </div>
    </div>
  )
}

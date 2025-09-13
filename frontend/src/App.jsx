import React, {useState, useEffect, useRef} from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export default function App(){
  const [messages, setMessages] = useState([
    {from: 'bot', text: 'Welcome to HealthPlus Lab — ask about tests, book appointments, or get offers.'}
  ])
  const [input, setInput] = useState('')
  const [name, setName] = useState('')
  const recognitionRef = useRef(null)

  useEffect(()=> {
    if(!('speechSynthesis' in window)){
      console.warn('No speech synthesis support in this browser')
    }
  },[])

  const speak = (text) => {
    if('speechSynthesis' in window){
      const ut = new SpeechSynthesisUtterance(text)
      window.speechSynthesis.cancel()
      window.speechSynthesis.speak(ut)
    }
  }

  const sendMessage = async (msg) => {
    setMessages(m=>[...m, {from:'user', text: msg}])
    setInput('')
    // call backend chat
    const res = await fetch(API + '/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({user: name, message: msg})
    })
    const data = await res.json()
    setMessages(m=>[...m, {from:'bot', text: data.reply}])
    speak(data.reply)
  }

  const startVoice = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if(!SpeechRecognition) return alert('SpeechRecognition not supported in this browser.')
    const recog = new SpeechRecognition()
    recog.lang = 'en-IN'
    recog.interimResults = false
    recog.onresult = (e) => {
      const text = e.results[0][0].transcript
      sendMessage(text)
    }
    recog.onerror = (e) => { console.error(e); alert('Voice error: '+e.error) }
    recog.start()
    recognitionRef.current = recog
  }

  const book = async () => {
    const test_id = prompt('Enter test id (blood / thyroid / diabetes):')
    const phone = prompt('Phone number:')
    const date = prompt('Preferred date (YYYY-MM-DD):')
    if(!name || !test_id || !phone || !date) return alert('Missing fields.')
    const res = await fetch(API + '/book', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, phone, test_id, date})
    })
    const data = await res.json()
    setMessages(m=>[...m, {from:'bot', text: `Booked ${data.test['name']} for ${data.booking_for} on ${data.date}. Offer: ${data.offer || 'None'}`}])
    speak(`Booked ${data.test['name']} on ${data.date}. ${data.offer || ''}`)
  }

  return (
    <div style={{fontFamily:'Arial', padding:20, maxWidth:800, margin:'0 auto'}}>
      <h2>HealthPlus Medical Lab — Chatbot</h2>
      <div style={{marginBottom:10}}>
        <label>Your name: </label>
        <input value={name} onChange={e=>setName(e.target.value)} placeholder="Optional for offers" />
        <button onClick={book} style={{marginLeft:10}}>Book Appointment</button>
        <button onClick={startVoice} style={{marginLeft:10}}>Voice Chat</button>
      </div>

      <div style={{border:'1px solid #ddd', padding:10, height:400, overflow:'auto', background:'#fafafa'}}>
        {messages.map((m,i)=>(
          <div key={i} style={{textAlign: m.from==='user' ? 'right' : 'left', margin:'8px 0'}}>
            <div style={{display:'inline-block', padding:10, borderRadius:8, background: m.from==='user' ? '#d1e7dd' : '#fff', boxShadow:'0 1px 2px rgba(0,0,0,0.05)'}}>
              <strong style={{display:'block', fontSize:12}}>{m.from}</strong>
              <div>{m.text}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{marginTop:10}}>
        <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter') sendMessage(input)}} placeholder="Type a message and press Enter" style={{width:'70%'}} />
        <button onClick={()=>sendMessage(input)} style={{marginLeft:10}}>Send</button>
      </div>
    </div>
  )
}

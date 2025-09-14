import React, { useEffect, useState } from 'react'

export default function LabInfo(){
  const [info, setInfo] = useState(null)

  useEffect(()=>{
    fetch('/api/labinfo')
      .then(r=>r.json())
      .then(d=>setInfo(d))
  },[])

  if(!info) return null

  return (
    <div style={{marginBottom:15, padding:10, background:'#f0f8ff', borderRadius:8}}>
      <h3>{info.name}</h3>
      <div>{info.address}</div>
      <a href={info.google_map} target="_blank" rel="noopener noreferrer">
        📍 View on Google Maps
      </a>
    </div>
  )
}

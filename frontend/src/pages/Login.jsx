import React, { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      if (isRegister) {
        await axios.post(`${API}/auth/register`, { email, password })
      }
      const params = new URLSearchParams()
      params.append('username', email)
      params.append('password', password)
      const res = await axios.post(`${API}/auth/login`, params)
      localStorage.setItem('token', res.data.access_token)
      navigate('/')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Error')
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '60px auto' }}>
      <h2>{isRegister ? 'Register' : 'Login'}</h2>
      <form onSubmit={submit}>
        <input placeholder='Email' value={email} onChange={(e)=>setEmail(e.target.value)} style={{ width: '100%', marginBottom: 8 }} />
        <input placeholder='Password' type='password' value={password} onChange={(e)=>setPassword(e.target.value)} style={{ width: '100%', marginBottom: 8 }} />
        {error && <div style={{ color: 'red', marginBottom: 8 }}>{error}</div>}
        <button type='submit' style={{ width: '100%' }}>{isRegister ? 'Create Account' : 'Login'}</button>
      </form>
      <button onClick={()=>setIsRegister(!isRegister)} style={{ marginTop: 12 }}>
        {isRegister ? 'Have an account? Login' : "Don't have an account? Register"}
      </button>
    </div>
  )
}



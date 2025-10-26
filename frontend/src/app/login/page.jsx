'use client' // Must add this for client-side hooks

import React, { useState } from 'react'
import api from '../../lib/api' // Updated import path
import { useRouter } from 'next/navigation' // Import useRouter

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter() // Use router instead of navigate

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      
      const params = new URLSearchParams()
      params.append('username', email)
      params.append('password', password)
      
      const res = await api.post('/auth/login', params)
      localStorage.setItem('token', res.data.access_token)
      
      router.push('/') // Use router.push() to navigate
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

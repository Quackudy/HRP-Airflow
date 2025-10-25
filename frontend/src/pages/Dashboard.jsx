import React, { useEffect, useState } from 'react'
import api from '../api'
import { Link } from 'react-router-dom'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Dashboard() {
  const [portfolios, setPortfolios] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', stock_tickers: '', objective_function: 'HRP', rebalance_interval: 'monthly' })

  const token = localStorage.getItem('token')
  
  // Redirect to login if no token
  if (!token) {
    window.location.href = '/login'
    return null
  }
  
  const load = async () => {
    try {
      const res = await api.get('/portfolios/')
      setPortfolios(res.data)
    } catch (err) {
      console.error('Failed to load portfolios:', err.response?.data || err.message)
      if (err.response?.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    }
  }

  useEffect(() => { load() }, [])

  const create = async (e) => {
    e.preventDefault()
    try {
      const payload = {
        ...form,
        stock_tickers: form.stock_tickers.split(',').map(s => s.trim()).filter(Boolean)
      }
  await api.post('/portfolios/', payload)
      setShowForm(false)
      setForm({ name: '', description: '', stock_tickers: '', objective_function: 'HRP', rebalance_interval: 'monthly' })
      load()
    } catch (err) {
      console.error('Failed to create portfolio:', err.response?.data || err.message)
      if (err.response?.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '40px auto' }}>
      <h2>Your Portfolios</h2>
      <button onClick={() => setShowForm(true)}>Create New Portfolio</button>
      {showForm && (
        <form onSubmit={create} style={{ marginTop: 12, border: '1px solid #ddd', padding: 12 }}>
          <input placeholder='Name' value={form.name} onChange={e=>setForm({...form, name:e.target.value})} style={{ width:'100%', marginBottom:8 }} />
          <input placeholder='Description' value={form.description} onChange={e=>setForm({...form, description:e.target.value})} style={{ width:'100%', marginBottom:8 }} />
          <input placeholder='Tickers CSV (e.g., AAPL,MSFT,GOOGL)' value={form.stock_tickers} onChange={e=>setForm({...form, stock_tickers:e.target.value})} style={{ width:'100%', marginBottom:8 }} />
          <input placeholder='Objective (HRP)' value={form.objective_function} onChange={e=>setForm({...form, objective_function:e.target.value})} style={{ width:'100%', marginBottom:8 }} />
          <select value={form.rebalance_interval} onChange={e=>setForm({...form, rebalance_interval:e.target.value})} style={{ width:'100%', marginBottom:8 }}>
            <option value='daily'>Daily</option>
            <option value='weekly'>Weekly</option>
            <option value='monthly'>Monthly</option>
            <option value='quarterly'>Quarterly</option>
          </select>
          <button type='submit'>Create</button>
        </form>
      )}
      <ul>
        {portfolios.map(p => (
          <li key={p.id} style={{ marginTop: 8 }}>
            <Link to={`/portfolio/${p.id}`}>{p.name}</Link>
          </li>
        ))}
      </ul>
    </div>
  )
}



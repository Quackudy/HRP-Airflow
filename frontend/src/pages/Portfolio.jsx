import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { useParams } from 'react-router-dom'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Portfolio() {
  const { id } = useParams()
  const [portfolio, setPortfolio] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const token = localStorage.getItem('token')
  const auth = { headers: { Authorization: `Bearer ${token}` } }

  const load = async () => {
    const [p, m] = await Promise.all([
      axios.get(`${API}/portfolios/${id}`, auth),
      axios.get(`${API}/portfolios/${id}/report`, auth)
    ])
    setPortfolio(p.data)
    setMetrics(m.data)
  }

  useEffect(() => { load() }, [id])

  return (
    <div style={{ maxWidth: 900, margin: '30px auto' }}>
      <h2>Portfolio {portfolio?.name}</h2>
      {metrics && (
        <div style={{ display:'flex', gap: 16 }}>
          <div>Sharpe: {metrics.sharpe.toFixed(2)}</div>
          <div>Max DD: {(metrics.max_drawdown*100).toFixed(2)}%</div>
          <div>CAGR: {(metrics.cagr*100).toFixed(2)}%</div>
        </div>
      )}
      <div style={{ marginTop: 16 }}>
        <iframe title='report' src={`${API}/portfolios/${id}/report/html`} style={{ width: '100%', height: 600, border: '1px solid #ddd' }} />
      </div>
    </div>
  )
}



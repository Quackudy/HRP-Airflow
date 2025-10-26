import React, { useEffect, useState } from 'react'
import api from '../api'
import { useParams } from 'react-router-dom'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Portfolio() {
  const { id } = useParams()
  const [portfolio, setPortfolio] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [reportHtml, setReportHtml] = useState(null)

  const load = async () => {
    const [p, m] = await Promise.all([
      api.get(`/portfolios/${id}`),
      api.get(`/portfolios/${id}/report`)
    ])
    setPortfolio(p.data)
    setMetrics(m.data)

    // Fetch HTML report via XHR so Authorization header is included (iframes can't set custom headers)
    try {
      const r = await api.get(`/portfolios/${id}/report/html`, { responseType: 'text' })
      setReportHtml(r.data)
    } catch (err) {
      if (err.response?.status === 404) {
        setError('This portfolio is not available. Please come back later.')
      }
      console.error('Failed to load HTML report:', err.response?.data || err.message)
      setReportHtml('<p>Unable to load report</p>')
    }
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
        {reportHtml ? (
          <div style={{ width: '100%', border: '1px solid #ddd', padding: 8 }} dangerouslySetInnerHTML={{ __html: reportHtml }} />
        ) : (
          <div>Loading report...</div>
        )}
      </div>
    </div>
  )
}



'use client' // Mark as client component

import React, { useEffect, useState } from 'react'
import api from '@/lib/api' // Updated path
import { useParams } from 'next/navigation' // Import from next/navigation

export default function Portfolio() {
  const params = useParams() // Get params hook
  const id = params.id // The 'id' comes from the [id] folder name
  
  const [portfolio, setPortfolio] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [reportHtml, setReportHtml] = useState(null)
  const [error, setError] = useState(null) // Added error state

  useEffect(() => {
    // Ensure id is available before loading
    if (!id) return 

    const load = async () => {
      try {
        const [p, m] = await Promise.all([
          api.get(`/portfolios/${id}`),
          api.get(`/portfolios/${id}/report`)
        ])
        setPortfolio(p.data)
        setMetrics(m.data)

        // Fetch HTML report
        const r = await api.get(`/portfolios/${id}/report/html`, { responseType: 'text' })
        setReportHtml(r.data)

      } catch (err) {
        if (err.response?.status === 404) {
          setError('This portfolio is not available. Please come back later.')
        } else {
          console.error('Failed to load HTML report:', err.response?.data || err.message)
          setReportHtml('<p>Unable to load report</p>')
        }
        
        // Handle 401 (though layout should catch it, good for defense)
        if (err.response?.status === 401) {
          localStorage.removeItem('token')
          window.location.href = '/login' // Simple redirect
        }
      }
    }
    
    load()
  }, [id]) // Dependency array includes id

  if (error) {
    return (
       <div style={{ maxWidth: 900, margin: '30px auto' }}>
         <h2>Error</h2>
         <p>{error}</p>
       </div>
    )
  }

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

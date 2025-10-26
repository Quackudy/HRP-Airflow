"use client"

import { useEffect, useState } from "react"
import api from "@/lib/api"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, TrendingUp, TrendingDown, Activity, BarChart3, Loader2 } from "lucide-react"

export default function Portfolio() {
  const params = useParams()
  const router = useRouter()
  const id = params.id

  const [portfolio, setPortfolio] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [reportHtml, setReportHtml] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return

    const load = async () => {
      try {
        const [p, m] = await Promise.all([api.get(`/portfolios/${id}`), api.get(`/portfolios/${id}/report`)])
        setPortfolio(p.data)
        setMetrics(m.data)

        const r = await api.get(`/portfolios/${id}/report/html`, { responseType: "text" })
        setReportHtml(r.data)
      } catch (err) {
        if (err.response?.status === 404) {
          setError("This portfolio is not available. Please come back later.")
        } else {
          console.error("Failed to load portfolio:", err.response?.data || err.message)
          setReportHtml('<p class="text-muted-foreground">Unable to load report</p>')
        }

        if (err.response?.status === 401) {
          localStorage.removeItem("token")
          router.push("/login")
        }
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [id, router])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm">
          <div className="container mx-auto flex h-16 items-center px-4">
            <Link href="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Portfolios
              </Button>
            </Link>
          </div>
        </header>
        <div className="container mx-auto px-4 py-12">
          <Card className="border-destructive/50">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
                <Activity className="h-8 w-8 text-destructive" />
              </div>
              <h3 className="mb-2 text-lg font-semibold">Error Loading Portfolio</h3>
              <p className="text-center text-sm text-muted-foreground">{error}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Portfolios
            </Button>
          </Link>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <BarChart3 className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-semibold">HRP</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Portfolio Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">{portfolio?.name}</h1>
          {portfolio?.description && <p className="mt-2 text-muted-foreground">{portfolio.description}</p>}
        </div>

        {/* Metrics Cards */}
        {metrics && (
          <div className="mb-8 grid gap-4 sm:grid-cols-3">
            <Card className="border-primary/20 bg-linear-to-br from-primary/5 to-transparent">
              <CardHeader className="pb-3">
                <CardDescription className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Sharpe Ratio
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{metrics.sharpe.toFixed(2)}</div>
                <p className="mt-1 text-xs text-muted-foreground">Risk-adjusted return metric</p>
              </CardContent>
            </Card>

            <Card
              className={`border-${metrics.max_drawdown < -0.2 ? "destructive" : "primary"}/20 bg-linear-to-br from-${metrics.max_drawdown < -0.2 ? "destructive" : "primary"}/5 to-transparent`}
            >
              <CardHeader className="pb-3">
                <CardDescription className="flex items-center gap-2">
                  <TrendingDown className="h-4 w-4" />
                  Max Drawdown
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className={`text-3xl font-bold ${metrics.max_drawdown < -0.2 ? "text-destructive" : ""}`}>
                  {(metrics.max_drawdown * 100).toFixed(2)}%
                </div>
                <p className="mt-1 text-xs text-muted-foreground">Largest peak-to-trough decline</p>
              </CardContent>
            </Card>

            <Card
              className={`border-${metrics.cagr > 0 ? "success" : "destructive"}/20 bg-linear-to-br from-${metrics.cagr > 0 ? "success" : "destructive"}/5 to-transparent`}
            >
              <CardHeader className="pb-3">
                <CardDescription className="flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  CAGR
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className={`text-3xl font-bold ${metrics.cagr > 0 ? "text-success" : "text-destructive"}`}>
                  {(metrics.cagr * 100).toFixed(2)}%
                </div>
                <p className="mt-1 text-xs text-muted-foreground">Compound annual growth rate</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Report Section */}
        <Card>
          <CardHeader>
            <CardTitle>Performance Report</CardTitle>
            <CardDescription>Detailed analysis and visualizations of portfolio performance</CardDescription>
          </CardHeader>
            <CardContent>
            {reportHtml ? (
              <iframe
                srcDoc={reportHtml}
                title="Portfolio Report"
                // Use Tailwind classes to style the iframe element itself
                className="w-full h-[800px] border rounded-md"
              />
            ) : (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

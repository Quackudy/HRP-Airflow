"use client"

import { useEffect, useState } from "react"
import api from "../../lib/api"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Plus, TrendingUp, BarChart3, LogOut, Loader2 } from "lucide-react"

export default function Dashboard() {
  const [portfolios, setPortfolios] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({
    name: "",
    description: "",
    stock_tickers: "",
    objective_function: "MV",
    rebalance_interval: "monthly",
    period: "2y",
  })
  const router = useRouter()

  const load = async () => {
    try {
      const res = await api.get("/portfolios/")
      setPortfolios(res.data)
    } catch (err) {
      console.error("Failed to load portfolios:", err.response?.data || err.message)
      if (err.response?.status === 401) {
        localStorage.removeItem("token")
        router.push("/login")
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const create = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      const payload = {
        ...form,
        stock_tickers: form.stock_tickers
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      }
      await api.post("/portfolios/", payload)
      setShowForm(false)
      setForm({
        name: "",
        description: "",
        stock_tickers: "",
        objective_function: "MV",
        rebalance_interval: "monthly",
        period: "2y",
      })
      load()
    } catch (err) {
      console.error("Failed to create portfolio:", err.response?.data || err.message)
      if (err.response?.status === 401) {
        localStorage.removeItem("token")
        router.push("/login")
      }
    } finally {
      setCreating(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem("token")
    router.push("/login")
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <BarChart3 className="h-5 w-5 text-primary-foreground" />
            </div>
            <h1 className="text-xl font-bold">HRP</h1>
          </div>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Your Portfolios</h2>
            <p className="mt-1 text-muted-foreground">Manage and track your investment portfolios</p>
          </div>

          <Dialog open={showForm} onOpenChange={setShowForm}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Create Portfolio
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Portfolio</DialogTitle>
                <DialogDescription>Configure your portfolio parameters and stock selections</DialogDescription>
              </DialogHeader>
              <form onSubmit={create} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Portfolio Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., Tech Growth Portfolio"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Brief description of your portfolio strategy"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tickers">Stock Tickers</Label>
                  <Input
                    id="tickers"
                    placeholder="AAPL, MSFT, GOOGL, AMZN"
                    value={form.stock_tickers}
                    onChange={(e) => setForm({ ...form, stock_tickers: e.target.value })}
                    required
                  />
                  <p className="text-xs text-muted-foreground">Enter comma-separated ticker symbols</p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="objective">Objective Function</Label>
                    <Input
                      id="objective"
                      placeholder="MV"
                      value={form.objective_function}
                      onChange={(e) => setForm({ ...form, objective_function: e.target.value })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="period">Period</Label>
                    <Input
                      id="period"
                      placeholder="2y"
                      value={form.period}
                      onChange={(e) => setForm({ ...form, period: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="rebalance">Rebalance Interval</Label>
                  <Select
                    value={form.rebalance_interval}
                    onValueChange={(value) => setForm({ ...form, rebalance_interval: value })}
                  >
                    <SelectTrigger id="rebalance">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="daily">Daily</SelectItem>
                      <SelectItem value="weekly">Weekly</SelectItem>
                      <SelectItem value="monthly">Monthly</SelectItem>
                      <SelectItem value="quarterly">Quarterly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setShowForm(false)} disabled={creating}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={creating}>
                    {creating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      "Create Portfolio"
                    )}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : portfolios.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                <TrendingUp className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="mb-2 text-lg font-semibold">No portfolios yet</h3>
              <p className="mb-4 text-center text-sm text-muted-foreground">
                Get started by creating your first portfolio
              </p>
              <Button onClick={() => setShowForm(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Portfolio
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {portfolios.map((p) => (
              <Link key={p.id} href={`/portfolio/${p.id}`}>
                <Card className="group cursor-pointer transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10">
                  <CardHeader>
                    <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                      <TrendingUp className="h-5 w-5" />
                    </div>
                    <CardTitle className="line-clamp-1">{p.name}</CardTitle>
                    <CardDescription className="line-clamp-2">
                      {p.description || "No description provided"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">View Details</span>
                      <span className="text-primary">→</span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

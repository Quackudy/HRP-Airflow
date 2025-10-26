'use client' // This layout is a client component

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function ProtectedLayout({ children }) {
  const router = useRouter()
  const [isAuthed, setIsAuthed] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
    } else {
      setIsAuthed(true)
    }
  }, [router])

  // Don't render children until auth status is confirmed
  if (!isAuthed) {
    return <div>Loading...</div> // Or a proper spinner component
  }

  // If authed, render the page
  return children
}

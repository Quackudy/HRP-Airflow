import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'

const isAuthed = () => !!localStorage.getItem('token')

const PrivateRoute = ({ children }) => {
  return isAuthed() ? children : <Navigate to="/login" />
}

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/portfolio/:id" element={<PrivateRoute><Portfolio /></PrivateRoute>} />
    </Routes>
  </BrowserRouter>
)



import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './components/Home.tsx'
import BlogDetail from './components/BlogDetail.tsx'
import './App.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/job/:jobId" element={<BlogDetail />} />
      </Routes>
    </Router>
  </React.StrictMode>,
)
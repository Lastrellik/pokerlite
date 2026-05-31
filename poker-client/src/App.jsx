import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Lobby from './components/Lobby'
import GamePage from './components/GamePage'
import AdminPage from './components/AdminPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Lobby />} />
        <Route path="/table/:tableId" element={<GamePage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './organizer.css'
import './pages.css'
import './customer-refine.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

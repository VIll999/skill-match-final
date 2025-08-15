import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppWithRouter from './AppWithRouter.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppWithRouter />
  </StrictMode>,
)

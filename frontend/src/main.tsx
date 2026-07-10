import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

/* Design tokens (must be first) */
import './styles/variables.css'
import './styles/reset.css'
import './styles/shared.css'
import './styles/layout.css'

/* Components */
import './styles/avatar.css'
import './styles/editor.css'

/* Pages */
import './styles/auth.css'
import './styles/home.css'
import './styles/library.css'
import './styles/detail.css'
import './styles/fork.css'
import './styles/profile.css'
import './styles/my-library.css'
import './styles/comment.css'
import './styles/commercial.css'
import './styles/resource.css'

/* Responsive (must be last) */
import './styles/responsive.css'

import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

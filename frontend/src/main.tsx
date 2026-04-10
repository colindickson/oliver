import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider, QueryCache, MutationCache } from '@tanstack/react-query'
import { ThemeProvider } from './contexts/ThemeContext'
import { MobileProvider } from './contexts/MobileContext'
import { ErrorBoundary } from './components/ErrorBoundary'
import App from './App.tsx'
import './index.css'

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => console.error('[Query error]', error),
  }),
  mutationCache: new MutationCache({
    onError: (error) => console.error('[Mutation error]', error),
  }),
  defaultOptions: {
    queries: {
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <ThemeProvider>
        <MobileProvider>
          <QueryClientProvider client={queryClient}>
            <BrowserRouter>
              <App />
            </BrowserRouter>
          </QueryClientProvider>
        </MobileProvider>
      </ThemeProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)

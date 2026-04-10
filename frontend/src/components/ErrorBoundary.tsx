import { Component, type ReactNode, type ErrorInfo } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-stone-50 dark:bg-stone-900 p-6">
          <div className="text-center max-w-sm">
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-terracotta-100 dark:bg-terracotta-900/30 flex items-center justify-center">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-terracotta-600 dark:text-terracotta-400" aria-hidden="true">
                <path d="M12 9v4M12 17h.01" strokeLinecap="round" />
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h1 className="text-lg font-semibold text-stone-800 dark:text-stone-100 mb-2">
              Something went wrong
            </h1>
            <p className="text-sm text-stone-500 dark:text-stone-400 mb-6">
              An unexpected error occurred. Please try reloading the page.
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-stone-800 text-white text-sm font-medium rounded-xl hover:bg-stone-700 transition-colors dark:bg-stone-700 dark:hover:bg-stone-600"
            >
              Reload
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

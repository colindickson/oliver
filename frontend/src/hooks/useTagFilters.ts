import { useSearchParams } from 'react-router-dom'
import { useCallback } from 'react'

export type PeriodOption = 7 | 30 | 90 | 'all'

export function useTagFilters() {
  const [searchParams, setSearchParams] = useSearchParams()

  // Read from URL, with defaults
  const periodParam = searchParams.get('period')
  const periodDays: PeriodOption =
    periodParam === '30d' ? 30 :
    periodParam === '90d' ? 90 :
    periodParam === 'all' ? 'all' : 7

  const showIncompleteOnly = searchParams.get('incomplete') === 'true'

  // Setters that update URL
  const setPeriodDays = useCallback((value: PeriodOption) => {
    setSearchParams(prev => {
      if (value === 7) {
        prev.delete('period')
      } else {
        prev.set('period', value === 'all' ? 'all' : `${value}d`)
      }
      return prev
    }, { replace: true })
  }, [setSearchParams])

  const setShowIncompleteOnly = useCallback((value: boolean) => {
    setSearchParams(prev => {
      if (value) {
        prev.set('incomplete', 'true')
      } else {
        prev.delete('incomplete')
      }
      return prev
    }, { replace: true })
  }, [setSearchParams])

  // Build filter params string for Links
  const filterParams = searchParams.toString()
  const filterParamsString = filterParams ? `?${filterParams}` : ''

  return {
    periodDays,
    showIncompleteOnly,
    setPeriodDays,
    setShowIncompleteOnly,
    filterParams: filterParamsString,
  }
}

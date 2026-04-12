import { useContext } from 'react'

import { FiltersContext } from './filters-context'

export function useGlobalFilters() {
  const context = useContext(FiltersContext)
  if (!context) {
    throw new Error('useGlobalFilters doit etre utilise a l interieur de FiltersProvider.')
  }
  return context
}

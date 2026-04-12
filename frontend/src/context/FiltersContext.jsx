import { useState } from 'react'

import { FiltersContext, initialFilters } from './filters-context'

export function FiltersProvider({ children }) {
  const [filters, setFilters] = useState(initialFilters)

  function updateFilter(name, value) {
    setFilters((current) => ({
      ...current,
      [name]: value,
    }))
  }

  function resetFilters() {
    setFilters(initialFilters)
  }

  const activeCount = Object.values(filters).filter(Boolean).length

  return (
    <FiltersContext.Provider
      value={{
        filters,
        updateFilter,
        resetFilters,
        activeCount,
      }}
    >
      {children}
    </FiltersContext.Provider>
  )
}

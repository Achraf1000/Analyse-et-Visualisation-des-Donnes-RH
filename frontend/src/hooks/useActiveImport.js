import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api'

export function useActiveImport() {
  const importsQuery = useQuery({
    queryKey: ['imports'],
    queryFn: api.listImports,
  })

  const importItems = importsQuery.data?.items || []
  const activeImport = importItems.find((item) => item.isActive) || null

  return {
    ...importsQuery,
    importItems,
    activeImport,
    hasImports: importItems.length > 0,
    hasActiveImport: Boolean(activeImport),
  }
}

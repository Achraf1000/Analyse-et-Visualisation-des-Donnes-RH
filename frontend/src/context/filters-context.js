import { createContext } from 'react'

export const FiltersContext = createContext(null)

export const initialFilters = {
  department: '',
  gender: '',
  tenureMin: '',
  tenureMax: '',
  ageMin: '',
  ageMax: '',
}

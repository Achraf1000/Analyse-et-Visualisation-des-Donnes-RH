import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { FilterBar } from '../components/FilterBar'
import { FiltersProvider } from '../context/FiltersContext'

describe('FilterBar', () => {
  it('met à jour les filtres globaux', () => {
    render(
      <FiltersProvider>
        <FilterBar options={{ departments: ['Finance'], genders: ['Femme', 'Homme'] }} />
      </FiltersProvider>,
    )

    fireEvent.change(screen.getByLabelText('Département'), { target: { value: 'Finance' } })
    fireEvent.change(screen.getByLabelText('Sexe'), { target: { value: 'Femme' } })

    expect(screen.getByDisplayValue('Finance')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Femme')).toBeInTheDocument()
  })
})

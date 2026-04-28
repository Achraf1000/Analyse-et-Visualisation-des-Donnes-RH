import { describe, expect, it } from 'vitest'

import { ApiError, buildFilterParams, isNoActiveImportError } from '../lib/api'

describe('api helpers', () => {
  it('preserves numeric zero values in filter params', () => {
    expect(
      buildFilterParams({
        department: '',
        gender: null,
        tenureMin: 0,
        tenureMax: 5,
        ageMin: 0,
        ageMax: '',
      }),
    ).toEqual({
      department: undefined,
      gender: undefined,
      tenureMin: 0,
      tenureMax: 5,
      ageMin: 0,
      ageMax: undefined,
    })
  })

  it('recognizes the no active import API error', () => {
    expect(isNoActiveImportError(new ApiError('Aucun import actif', 409, 'Aucun import actif'))).toBe(true)
    expect(isNoActiveImportError(new Error('generic'))).toBe(false)
  })
})

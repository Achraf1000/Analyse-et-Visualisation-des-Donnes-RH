import { useGlobalFilters } from '../context/useGlobalFilters'

const filterFields = [
  { name: 'department', label: 'Département', type: 'select' },
  { name: 'gender', label: 'Sexe', type: 'select' },
  { name: 'tenureMin', label: 'Ancienneté min', type: 'number' },
  { name: 'tenureMax', label: 'Ancienneté max', type: 'number' },
  { name: 'ageMin', label: 'Âge min', type: 'number' },
  { name: 'ageMax', label: 'Âge max', type: 'number' },
]

export function FilterBar({ options = { departments: [], genders: [] } }) {
  const { filters, updateFilter, resetFilters, activeCount } = useGlobalFilters()

  return (
    <section className="filter-panel" aria-label="Filtres globaux">
      <div className="filter-panel-header">
        <div>
          <p className="eyebrow">Filtres</p>
          <h3>Périmètre d’analyse</h3>
        </div>
        <button className="ghost-button" type="button" onClick={resetFilters}>
          Réinitialiser {activeCount > 0 ? `(${activeCount})` : ''}
        </button>
      </div>

      <div className="filter-grid">
        {filterFields.map((field) => (
          <label className="field" key={field.name}>
            <span>{field.label}</span>
            {field.type === 'select' ? (
              <select
                value={filters[field.name]}
                onChange={(event) => updateFilter(field.name, event.target.value)}
              >
                <option value="">Tous</option>
                {(field.name === 'department' ? options.departments : options.genders).map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="number"
                value={filters[field.name]}
                onChange={(event) => updateFilter(field.name, event.target.value)}
                placeholder="Tous"
              />
            )}
          </label>
        ))}
      </div>
    </section>
  )
}

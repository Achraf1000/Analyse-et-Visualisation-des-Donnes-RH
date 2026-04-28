import { Link } from 'react-router-dom'

import { useAuth } from '../context/useAuth'

export function ActiveImportNotice({ hasImports }) {
  const { hasRole } = useAuth()
  const canManageImports = hasRole('ADMIN_RH')

  return (
    <section className="empty-card empty-card-emphasis">
      <h3>{hasImports ? 'Aucun dataset actif' : 'Aucun dataset disponible'}</h3>
      <p>
        {canManageImports
          ? hasImports
            ? "Corrigez les anomalies puis activez un import depuis l'ecran Import & Validation pour debloquer les KPI, analyses, predictions et le rapport."
            : 'Importez un premier fichier CSV puis activez un dataset valide pour afficher les KPI, analyses, predictions et le rapport.'
          : "Aucun dataset actif n'est disponible. Demandez a l'administrateur RH d'importer et d'activer un dataset valide."}
      </p>
      {canManageImports ? (
        <Link className="primary-button link-button" to="/imports">
          Ouvrir l'ecran d'import
        </Link>
      ) : null}
    </section>
  )
}

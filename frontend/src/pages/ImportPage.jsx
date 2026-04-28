import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { DataTable } from '../components/DataTable'
import { api } from '../lib/api'
import { formatDateTime } from '../lib/format'

const AUTO_FIXABLE_ISSUE_CODES = new Set(['duplicate_employee_id'])

function issueKey(issue) {
  return `${issue.recordId}:${issue.fieldName}`
}

function buildDuplicateEmployeeIdPatches(issues) {
  const duplicateIssues = issues
    .filter((issue) => issue.issueCode === 'duplicate_employee_id' && issue.fieldName === 'employee_id' && issue.recordId)
    .sort((first, second) => {
      const firstValue = String(first.currentValue || '').localeCompare(String(second.currentValue || ''))
      if (firstValue !== 0) return firstValue
      return (first.rowIndex || 0) - (second.rowIndex || 0)
    })

  const groups = duplicateIssues.reduce((accumulator, issue) => {
    const value = String(issue.currentValue || '').trim()
    if (!value) return accumulator
    const key = value.toLowerCase()
    const group = accumulator.get(key) || []
    group.push(issue)
    accumulator.set(key, group)
    return accumulator
  }, new Map())

  const usedValues = new Set(duplicateIssues.map((issue) => String(issue.currentValue || '').trim().toLowerCase()).filter(Boolean))
  const patches = []

  groups.forEach((group) => {
    group.forEach((issue, index) => {
      if (index === 0) return

      const baseValue = String(issue.currentValue || '').trim()
      const rowSuffix = issue.rowIndex ? `L${issue.rowIndex}` : `${index + 1}`
      let nextValue = `${baseValue}-${rowSuffix}`
      let collisionIndex = 2

      while (usedValues.has(nextValue.toLowerCase())) {
        nextValue = `${baseValue}-${rowSuffix}-${collisionIndex}`
        collisionIndex += 1
      }

      usedValues.add(nextValue.toLowerCase())
      patches.push({
        recordId: issue.recordId,
        fieldName: issue.fieldName,
        value: nextValue,
        rowIndex: issue.rowIndex,
        previousValue: baseValue,
      })
    })
  })

  return patches
}

function IssueInput({ issue, drafts, setDrafts, onSave, pendingKey, disabled }) {
  const key = `${issue.recordId}:${issue.fieldName}`
  const value = drafts[key] ?? issue.currentValue ?? ''
  const isPending = pendingKey === key

  if (!issue.recordId || !issue.fieldName) {
    return <span className="muted-copy">Non modifiable</span>
  }

  return (
    <div className="issue-editor">
      <input
        value={value}
        onChange={(event) =>
          setDrafts((current) => ({
            ...current,
            [key]: event.target.value,
          }))
        }
      />
      <button className="primary-button small" type="button" onClick={() => onSave(issue, value)} disabled={disabled || isPending}>
        {isPending ? 'Sauvegarde...' : 'Sauver'}
      </button>
    </div>
  )
}

export function ImportPage() {
  const queryClient = useQueryClient()
  const [selectedImportId, setSelectedImportId] = useState(null)
  const [file, setFile] = useState(null)
  const [page, setPage] = useState(1)
  const [drafts, setDrafts] = useState({})
  const [feedback, setFeedback] = useState(null)
  const [pendingIssueKey, setPendingIssueKey] = useState('')

  const importsQuery = useQuery({
    queryKey: ['imports'],
    queryFn: api.listImports,
  })

  const importItems = importsQuery.data?.items || []
  const effectiveImportId = selectedImportId ?? importItems[0]?.importId ?? null

  const detailQuery = useQuery({
    queryKey: ['import-detail', effectiveImportId],
    queryFn: () => api.getImport(effectiveImportId),
    enabled: Boolean(effectiveImportId),
  })

  const issuesQuery = useQuery({
    queryKey: ['import-issues', effectiveImportId, page],
    queryFn: () => api.getImportIssues(effectiveImportId, page),
    enabled: Boolean(effectiveImportId),
  })

  const uploadMutation = useMutation({
    mutationFn: api.uploadCsv,
    onSuccess: async (createdImport) => {
      setSelectedImportId(createdImport.importId)
      setPage(1)
      setFile(null)
      await queryClient.invalidateQueries({ queryKey: ['imports'] })
      await queryClient.invalidateQueries({ queryKey: ['import-detail', createdImport.importId] })
      await queryClient.invalidateQueries({ queryKey: ['import-issues'] })
    },
  })

  const patchMutation = useMutation({
    mutationFn: ({ importId, recordId, payload }) => api.patchRecord(importId, recordId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['imports'] })
      await queryClient.invalidateQueries({ queryKey: ['import-detail', effectiveImportId] })
      await queryClient.invalidateQueries({ queryKey: ['import-issues', effectiveImportId] })
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      await queryClient.invalidateQueries({ queryKey: ['predictions'] })
    },
  })

  const autoFixMutation = useMutation({
    mutationFn: async (importId) => {
      const pageSize = 200
      const issues = []
      let currentPage = 1
      let total = 0

      do {
        const response = await api.getImportIssues(importId, currentPage, pageSize)
        issues.push(...response.items)
        total = response.total || 0
        currentPage += 1
      } while (issues.length < total)

      const patches = buildDuplicateEmployeeIdPatches(issues)
      for (const patch of patches) {
        await api.patchRecord(importId, patch.recordId, { [patch.fieldName]: patch.value })
      }

      return { patchedCount: patches.length }
    },
    onSuccess: async ({ patchedCount }) => {
      await queryClient.invalidateQueries({ queryKey: ['imports'] })
      await queryClient.invalidateQueries({ queryKey: ['import-detail', effectiveImportId] })
      await queryClient.invalidateQueries({ queryKey: ['import-issues', effectiveImportId] })
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      await queryClient.invalidateQueries({ queryKey: ['predictions'] })
      setDrafts({})
      setFeedback({
        type: patchedCount ? 'success' : 'info',
        message: patchedCount
          ? `${patchedCount} doublon(s) employee_id corrige(s). Validation relancee.`
          : 'Aucun doublon employee_id automatisable trouve.',
      })
    },
    onError: (error) => {
      setFeedback({ type: 'error', message: error.message })
    },
  })

  const activateMutation = useMutation({
    mutationFn: api.activateImport,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['imports'] })
      await queryClient.invalidateQueries({ queryKey: ['import-detail', effectiveImportId] })
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      await queryClient.invalidateQueries({ queryKey: ['predictions'] })
    },
  })

  const currentImport = detailQuery.data

  async function handleUpload(event) {
    event.preventDefault()
    if (!file) {
      return
    }
    await uploadMutation.mutateAsync(file)
  }

  async function handleSave(issue, value) {
    if (!issue.recordId || !issue.fieldName || !effectiveImportId) {
      return
    }
    const trimmedValue = String(value ?? '').trim()
    if (!trimmedValue) {
      setFeedback({ type: 'error', message: 'La correction ne peut pas etre vide.' })
      return
    }

    const key = issueKey(issue)
    setPendingIssueKey(key)
    setFeedback(null)
    try {
      await patchMutation.mutateAsync({
        importId: effectiveImportId,
        recordId: issue.recordId,
        payload: { [issue.fieldName]: trimmedValue },
      })
      setDrafts((current) => {
        const next = { ...current }
        delete next[key]
        return next
      })
      setFeedback({ type: 'success', message: `Correction sauvegardee pour la ligne ${issue.rowIndex}. Validation relancee.` })
    } catch (error) {
      setFeedback({ type: 'error', message: error.message })
    } finally {
      setPendingIssueKey('')
    }
  }

  async function handleAutoFixDuplicates() {
    if (!effectiveImportId) {
      return
    }
    setFeedback(null)
    try {
      await autoFixMutation.mutateAsync(effectiveImportId)
    } catch {
      // Feedback is set in the mutation onError handler.
    }
  }

  async function handleActivate() {
    if (!effectiveImportId) {
      return
    }
    await activateMutation.mutateAsync(effectiveImportId)
  }

  const issueColumns = [
    {
      accessorKey: 'rowIndex',
      header: 'Ligne',
    },
    {
      accessorKey: 'fieldName',
      header: 'Champ',
    },
    {
      accessorKey: 'message',
      header: 'Anomalie',
    },
    {
      accessorKey: 'currentValue',
      header: 'Correction',
      cell: ({ row }) => (
        <IssueInput
          issue={row.original}
          drafts={drafts}
          setDrafts={setDrafts}
          onSave={handleSave}
          pendingKey={pendingIssueKey}
          disabled={patchMutation.isPending || autoFixMutation.isPending}
        />
      ),
    },
  ]

  const visibleAutoFixableCount =
    issuesQuery.data?.items.filter((issue) => AUTO_FIXABLE_ISSUE_CODES.has(issue.issueCode)).length || 0

  const canActivate =
    currentImport &&
    !currentImport.missingRequiredFields.length &&
    currentImport.validationSummary.blocking_issues === 0

  return (
    <div className="page-stack">
      <section className="hero-panel hero-panel-split">
        <div>
          <p className="eyebrow">US1 · US2</p>
          <h2>Importer, verifier et corriger les donnees RH</h2>
          <p className="muted-copy">
            Deposez un CSV, laissez l application mapper les colonnes automatiquement puis corrigez les incoherences
            detectees.
          </p>
        </div>

        <form className="upload-panel" onSubmit={handleUpload}>
          <label className="field">
            <span>Fichier CSV</span>
            <input type="file" accept=".csv" onChange={(event) => setFile(event.target.files?.[0] || null)} />
          </label>
          <button className="primary-button" type="submit" disabled={!file || uploadMutation.isPending}>
            {uploadMutation.isPending ? 'Import en cours...' : 'Importer le fichier'}
          </button>
          {uploadMutation.isError ? <span className="error-text">{uploadMutation.error.message}</span> : null}
        </form>
      </section>

      <div className="import-layout">
        <aside className="history-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Historique</p>
              <h3>Imports disponibles</h3>
            </div>
          </div>

          {importsQuery.isLoading ? <div className="loading-card">Chargement des imports...</div> : null}

          {importItems.map((item) => (
            <button
              type="button"
              key={item.importId}
              className={`history-item ${effectiveImportId === item.importId ? 'is-selected' : ''}`}
              onClick={() => {
                setSelectedImportId(item.importId)
                setPage(1)
              }}
            >
              <strong>{item.filename}</strong>
              <span>{formatDateTime(item.uploadedAt)}</span>
              <span className={`status-pill ${item.isActive ? 'status-active' : 'status-muted'}`}>
                {item.isActive ? 'Actif' : item.status}
              </span>
            </button>
          ))}
        </aside>

        <section className="import-main">
          {detailQuery.isLoading ? <div className="loading-card">Chargement de l import...</div> : null}
          {detailQuery.isError ? <div className="empty-card">{detailQuery.error.message}</div> : null}

          {currentImport ? (
            <>
              <div className="summary-grid">
                <article className="summary-card">
                  <span>Total lignes</span>
                  <strong>{currentImport.validationSummary.total_rows}</strong>
                </article>
                <article className="summary-card">
                  <span>Lignes valides</span>
                  <strong>{currentImport.validationSummary.valid_rows}</strong>
                </article>
                <article className="summary-card">
                  <span>Lignes invalides</span>
                  <strong>{currentImport.validationSummary.invalid_rows}</strong>
                </article>
                <article className="summary-card">
                  <span>Erreurs bloquantes</span>
                  <strong>{currentImport.validationSummary.blocking_issues}</strong>
                </article>
              </div>

              <div className="info-grid">
                <section className="detail-card">
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">Mapping</p>
                      <h3>Colonnes detectees</h3>
                    </div>
                    <button className="primary-button" type="button" disabled={!canActivate || activateMutation.isPending} onClick={handleActivate}>
                      {activateMutation.isPending ? 'Activation...' : 'Activer ce dataset'}
                    </button>
                  </div>

                  <div className="mapping-list">
                    {Object.entries(currentImport.detectedMapping).map(([key, value]) => (
                      <div className="mapping-item" key={key}>
                        <span>{key}</span>
                        <strong>{value || 'Non detecte'}</strong>
                      </div>
                    ))}
                  </div>

                  {currentImport.missingRequiredFields.length ? (
                    <div className="error-banner">
                      Colonnes requises manquantes : {currentImport.missingRequiredFields.join(', ')}
                    </div>
                  ) : null}
                  {activateMutation.isError ? <div className="error-banner">{activateMutation.error.message}</div> : null}
                </section>

                <section className="detail-card">
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">Validation</p>
                      <h3>Anomalies a corriger</h3>
                    </div>
                    <div className="validation-actions">
                      <button
                        className="ghost-button"
                        type="button"
                        disabled={!effectiveImportId || autoFixMutation.isPending || patchMutation.isPending}
                        onClick={handleAutoFixDuplicates}
                      >
                        {autoFixMutation.isPending ? 'Correction...' : 'Corriger doublons auto'}
                      </button>
                      <span className="muted-copy">
                        Page {page} / {Math.max(1, Math.ceil((issuesQuery.data?.total || 0) / 25))}
                      </span>
                    </div>
                  </div>

                  {feedback ? (
                    <div
                      className={
                        feedback.type === 'error'
                          ? 'error-banner'
                          : feedback.type === 'success'
                            ? 'success-banner'
                            : 'info-banner'
                      }
                    >
                      {feedback.message}
                    </div>
                  ) : null}

                  {visibleAutoFixableCount ? (
                    <div className="info-banner">
                      {visibleAutoFixableCount} doublon(s) employee_id visible(s). La correction automatique garde la
                      premiere occurrence et renomme les suivantes.
                    </div>
                  ) : null}

                  {issuesQuery.isLoading ? <div className="loading-card">Chargement des anomalies...</div> : null}
                  {issuesQuery.data ? (
                    <>
                      <DataTable
                        data={issuesQuery.data.items}
                        columns={issueColumns}
                        emptyMessage="Aucune incoherence bloquante sur cet import."
                      />

                      <div className="pager">
                        <button className="ghost-button" type="button" disabled={page === 1} onClick={() => setPage((current) => current - 1)}>
                          Page precedente
                        </button>
                        <button
                          className="ghost-button"
                          type="button"
                          disabled={page * 25 >= (issuesQuery.data.total || 0)}
                          onClick={() => setPage((current) => current + 1)}
                        >
                          Page suivante
                        </button>
                      </div>
                    </>
                  ) : null}
                </section>
              </div>
            </>
          ) : (
            <div className="empty-card">Importez un premier fichier CSV pour demarrer.</div>
          )}
        </section>
      </div>
    </div>
  )
}

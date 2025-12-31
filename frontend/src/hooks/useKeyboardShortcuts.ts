import { useHotkeys } from 'react-hotkeys-hook'
import { useNavigate } from 'react-router-dom'

interface UseKeyboardShortcutsOptions {
  onOpenHelp?: () => void
  onFocusSearch?: () => void
  onAddPatient?: () => void
  onAddEpisode?: () => void
}

/**
 * Custom hook for global keyboard shortcuts
 * - mod+1-4: Navigate to different pages
 * - shift+/: Open help dialog
 * - mod+k: Focus search (context-aware)
 * - mod+shift+p: Add patient (on Patients page)
 * - mod+shift+e: Add episode (on Episodes page)
 *
 * @param options - Configuration for keyboard shortcuts
 */
export function useKeyboardShortcuts(options?: UseKeyboardShortcutsOptions) {
  const navigate = useNavigate()

  // Page navigation shortcuts
  useHotkeys('mod+1', () => navigate('/'), { preventDefault: true, enableOnFormTags: ['INPUT', 'TEXTAREA', 'SELECT'] })
  useHotkeys('mod+2', () => navigate('/patients'), { preventDefault: true, enableOnFormTags: ['INPUT', 'TEXTAREA', 'SELECT'] })
  useHotkeys('mod+3', () => navigate('/episodes'), { preventDefault: true, enableOnFormTags: ['INPUT', 'TEXTAREA', 'SELECT'] })
  useHotkeys('mod+4', () => navigate('/reports'), { preventDefault: true, enableOnFormTags: ['INPUT', 'TEXTAREA', 'SELECT'] })

  // Help dialog - already handled in App.tsx, but we keep this for consistency
  // Note: Help is handled globally in App.tsx with shift+/

  // Search focus (Cmd/Ctrl+K)
  useHotkeys(
    'mod+k',
    (e) => {
      e.preventDefault()
      if (options?.onFocusSearch) {
        options.onFocusSearch()
      }
    },
    {
      preventDefault: true,
      enabled: !!options?.onFocusSearch,
      enableOnFormTags: ['INPUT', 'TEXTAREA', 'SELECT']
    }
  )

  // Quick action: Add Patient (Cmd/Ctrl+Shift+P)
  useHotkeys(
    'mod+shift+p',
    (e) => {
      e.preventDefault()
      if (options?.onAddPatient) {
        options.onAddPatient()
      }
    },
    {
      preventDefault: true,
      enabled: !!options?.onAddPatient,
      enableOnFormTags: ['INPUT', 'TEXTAREA', 'SELECT']
    }
  )

  // Quick action: Add Episode (Cmd/Ctrl+Shift+E)
  useHotkeys(
    'mod+shift+e',
    (e) => {
      e.preventDefault()
      if (options?.onAddEpisode) {
        options.onAddEpisode()
      }
    },
    {
      preventDefault: true,
      enabled: !!options?.onAddEpisode,
      enableOnFormTags: ['INPUT', 'TEXTAREA', 'SELECT']
    }
  )
}

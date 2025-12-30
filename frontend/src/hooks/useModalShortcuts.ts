import { useHotkeys } from 'react-hotkeys-hook'

interface UseModalShortcutsOptions {
  onClose: () => void
  onSubmit?: () => void
  isOpen: boolean
  canSubmit?: boolean
}

/**
 * Custom hook for modal keyboard shortcuts
 * - Escape: Close modal
 * - Cmd/Ctrl+Enter: Submit form (if onSubmit provided and canSubmit is true)
 *
 * @param options - Configuration for modal shortcuts
 * @param options.onClose - Callback to close the modal
 * @param options.onSubmit - Optional callback to submit the form
 * @param options.isOpen - Whether the modal is currently open
 * @param options.canSubmit - Whether form submission is allowed (default: true)
 */
export function useModalShortcuts(options: UseModalShortcutsOptions) {
  const { onClose, onSubmit, isOpen, canSubmit = true } = options

  // Escape to close modal
  // enableOnFormTags allows Escape to work even when focus is in an input field
  useHotkeys(
    'escape',
    () => {
      if (isOpen) {
        onClose()
      }
    },
    {
      enabled: isOpen,
      enableOnFormTags: true,
      preventDefault: true
    },
    [isOpen, onClose]
  )

  // Cmd/Ctrl+Enter to submit form
  // enableOnFormTags allows the shortcut to work when focus is in an input field
  useHotkeys(
    'mod+enter',
    () => {
      if (isOpen && canSubmit && onSubmit) {
        onSubmit()
      }
    },
    {
      enabled: isOpen && canSubmit && !!onSubmit,
      enableOnFormTags: true,
      preventDefault: true
    },
    [isOpen, canSubmit, onSubmit]
  )
}

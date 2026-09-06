import { Toaster as SonnerToaster, toast } from 'sonner'
import { useThemeStore } from '../../stores/theme'

export function Toaster() {
  const rawTheme = useThemeStore((s) => s.theme)

  const resolved: 'light' | 'dark' =
    rawTheme === 'system'
      ? typeof window !== 'undefined' &&
        typeof window.matchMedia === 'function' &&
        window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      : rawTheme

  return (
    <SonnerToaster
      theme={resolved}
      position="bottom-right"
      richColors={false}
      toastOptions={{
        classNames: {
          toast:
            'bg-surface-card text-on-surface border border-border rounded-card shadow-lg',
          error: 'bg-danger-subtle text-danger border-danger/30',
          success: 'bg-success-subtle text-on-surface border-success/30',
          warning: 'bg-warning-subtle text-on-surface border-warning/30',
          info: 'bg-info-subtle text-on-surface border-info/30',
        },
      }}
    />
  )
}

// eslint-disable-next-line react-refresh/only-export-components -- toast re-export paired with Toaster component
export { toast }

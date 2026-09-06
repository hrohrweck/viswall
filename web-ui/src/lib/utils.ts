import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge Tailwind utility classes, resolving conflicts (tailwind-merge)
 * and conditionally joining (clsx).
 *
 * Use for token-class composition across the UI kit — never hand-concat
 * conditional class strings.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

export function getErrMsg(err: unknown): string {
  if (
    typeof err === 'object' &&
    err !== null &&
    'response' in err
  ) {
    const response = (err as { response?: { data?: { detail?: string } } }).response
    if (
      typeof response === 'object' &&
      response !== null &&
      'data' in response
    ) {
      const data = (response as { data?: { detail?: string } }).data
      if (
        typeof data === 'object' &&
        data !== null &&
        'detail' in data &&
        typeof (data as { detail?: unknown }).detail === 'string'
      ) {
        return (data as { detail: string }).detail
      }
    }
  }

  if (err instanceof Error) {
    return err.message
  }

  if (typeof err === 'string') {
    return err
  }

  return 'An unexpected error occurred'
}

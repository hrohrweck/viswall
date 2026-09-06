import { useEffect, useCallback, useRef } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { ErrorBoundary } from './ui/ErrorBoundary'
import { Toaster } from './ui/Toaster'
import { CommandPalette } from './ui/CommandPalette'
import { useSidebarStore } from '../stores/sidebar'
import { useIsDesktop } from '../hooks/useIsDesktop'

export function Layout() {
  const location = useLocation()
  const mobileOpen = useSidebarStore((s) => s.mobileOpen)
  const setMobileOpen = useSidebarStore((s) => s.setMobileOpen)
  const isDesktop = useIsDesktop()

  const closeMobile = useCallback(() => setMobileOpen(false), [setMobileOpen])
  const prevPathname = useRef(location.pathname)

  useEffect(() => {
    if (prevPathname.current !== location.pathname) {
      closeMobile()
    }
    prevPathname.current = location.pathname
  }, [location.pathname, closeMobile])

  useEffect(() => {
    if (mobileOpen && !isDesktop) {
      document.body.style.overflow = 'hidden'
      return () => { document.body.style.overflow = '' }
    }
    document.body.style.overflow = ''
  }, [mobileOpen, isDesktop])

  useEffect(() => {
    if (!mobileOpen) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeMobile()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [mobileOpen, closeMobile])

  useEffect(() => {
    if (isDesktop && mobileOpen) closeMobile()
  }, [isDesktop, mobileOpen, closeMobile])

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:top-3 focus:left-3 focus:px-4 focus:py-2 focus:rounded-card focus:bg-primary focus:text-primary-fg focus:text-sm focus:font-medium focus:shadow-lg"
      >
        Skip to content
      </a>
      <Header />
      <div className="flex flex-1">
        {!isDesktop && mobileOpen && (
          <div
            data-testid="sidebar-scrim"
            className="fixed inset-0 z-40 bg-black/50"
            onClick={closeMobile}
            aria-hidden="true"
          />
        )}
        <div
          className={
            isDesktop
              ? 'shrink-0'
              : `fixed inset-y-0 left-0 z-50 w-64 transition-transform duration-200 ${
                  mobileOpen ? 'translate-x-0' : 'translate-x-[-100%]'
                }`
          }
        >
          <Sidebar />
        </div>
        <main id="main-content" className="flex-1 p-4 lg:p-6 max-w-[1440px] w-full">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
      <Toaster />
      <CommandPalette />
    </div>
  )
}
